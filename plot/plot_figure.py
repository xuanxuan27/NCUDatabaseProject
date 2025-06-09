import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import os
from plot.data_access import get_db_connection, fetch_stock_data
from plot.db_config import db_cfg
import granville_toolkit as gt

import warnings
# 忽略 UserWarning 和 FutureWarning
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 1. 中文字型設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_candle_and_volume_chart(
    df: pd.DataFrame,
    stock_code: int,
    save_path: str = ".",
    ma_columns: list = None
) -> str:
    """
    繪製 K 棒＋成交量＋MA，並存檔。
    ma_columns: list of MA column names in df (e.g. ['MA5','MA20','MA60'])
    """
    if ma_columns is None:
        ma_columns = ['MA5', 'MA20', 'MA60']

    addplots = []
    for col, color in zip(ma_columns, ['blue', 'orange', 'green']):
        if col in df.columns and df[col].notna().any():
            addplots.append(
                mpf.make_addplot(df[col], color=color, width=1, label=col)
            )

    # 畫圖：K 棒 + 成交量 + 各種 MA
    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=True,
        title=str(stock_code),
        addplot=addplots,
        style='yahoo',
        panel_ratios=(3, 1),
        figsize=(12, 8),
        returnfig=True
    )
    ax = axes[0]

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper left')

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return save_path

def plot_bollinger(
    df: pd.DataFrame,
    window: int = 20,
    num_std: int = 2,
    price_col: str = 'Close',
    save_path: str = "."
) -> str:

    ma = df[price_col].rolling(window).mean()
    std = df[price_col].rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df[price_col], label=price_col)
    ax.plot(df.index, ma, label=f'MA{window}')
    ax.plot(df.index, upper, label='Upper Band')
    ax.plot(df.index, lower, label='Lower Band')
    ax.set_title('Bollinger Bands')
    ax.legend()

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path

def plot_rsi(
    df: pd.DataFrame,
    period: int = 14,
    price_col: str = 'Close',
    save_path: str = "."
) -> str:

    delta = df[price_col].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df.index, rsi, label='RSI')
    ax.axhline(70, linestyle='--', label='Overbought')
    ax.axhline(30, linestyle='--', label='Oversold')
    ax.set_title('Relative Strength Index')
    ax.legend()

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return save_path

def plot_kd(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
    low_col: str = 'Low',     # 傳入用來計算最低值的欄位
    high_col: str = 'High',   # 傳入用來計算最高值的欄位
    close_col: str = 'Close', # 傳入用來計算 RSV 的欄位
    save_path: str = None
):
    low_min = df[low_col].rolling(k_period).min()
    high_max = df[high_col].rolling(k_period).max()
    rsv = (df[close_col] - low_min) / (high_max - low_min) * 100

    k = rsv.ewm(span=d_period, adjust=False).mean()
    d = k.ewm(span=d_period, adjust=False).mean()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df.index, k, label='%K')
    ax.plot(df.index, d, label='%D')
    ax.set_title('Stochastic Oscillator (KD)')
    ax.legend()

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return save_path

def plot_all_charts(
    stock_code: int,
    start_date: str,
    end_date: str,
    db_config: dict,
    save_path: str = ".",
    bollinger_window: int = 20,
    rsi_period: int = 14,
    kd_k_period: int = 14,
    kd_d_period: int = 3
) -> dict:
    """
    依序生成 K 線圖、布林帶、RSI、KD 圖，回傳各檔案路徑。
    可以傳入布林帶、RSI、KD 的週期參數，並帶入預設值。
    """
    conn = get_db_connection(**db_config)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()

    if df.empty:
        print("查無資料")
        return {}

    results = {}
    # K 線與成交量
    results['candle'] = plot_candle_and_volume_chart(
        df.copy(),
        stock_code,
        save_path = save_path
    )
    # Bollinger
    results['bollinger'] = plot_bollinger(
        df,
        bollinger_window,
        save_path = save_path
    )
    # RSI
    results['rsi'] = plot_rsi(
        df,
        period=rsi_period,
        save_path = save_path
    )
    # KD
    results['kd'] = plot_kd(
        df,
        k_period=kd_k_period,
        d_period=kd_d_period,
        save_path = save_path
    )

    return results

def plot_granville_charts(
    stock_code: int,
    start_date: str,
    end_date: str,
    db_config: dict,
    save_path: str = ".",
    ma_window: int = 20,
    vol_ma_window: int = 20
) -> str:  # 回傳完整檔案路徑
    conn = get_db_connection(**db_config)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()
    if df.empty:
        print("查無資料")
        return ""

    ma_col_name = f"MA{ma_window}"
    vol_ma_col_name = f"Vol_MA{vol_ma_window}"

    if ma_col_name not in df.columns:
        df = gt.moving_average(df, window=ma_window, column='Close', out_col=ma_col_name)

    if vol_ma_col_name not in df.columns:
        df[vol_ma_col_name] = df['Volume'].rolling(vol_ma_window).mean()

    lower_ma_col = ma_col_name.lower()
    df[lower_ma_col] = df[ma_col_name]
    lower_vol_ma_col = vol_ma_col_name.lower()
    df[lower_vol_ma_col] = df[vol_ma_col_name]

    df = gt.granville_eight_rules(
        df,
        ma_col=lower_ma_col,
        price_col='Close',
        vol_col='Volume',
        vol_ma_col=lower_vol_ma_col,
        out_col='granville_signal'
    )

    df['Deviation'] = (df['Close'] - df[ma_col_name]) / df[ma_col_name] * 100
    df['Slope'] = df[ma_col_name].diff()
    df[vol_ma_col_name] = df['Volume'].rolling(vol_ma_window).mean()

    rule_defs = {
        'R1': {'mask': df['granville_signal'] == 1, 'marker': '^', 'color': 'green'},
        'R2': {'mask': df['granville_signal'] == 2, 'marker': '^', 'color': 'blue'},
        'R3': {'mask': df['granville_signal'] == 3, 'marker': '^', 'color': 'purple'},
        'R4': {'mask': df['granville_signal'] == 4, 'marker': '^', 'color': 'cyan'},
        'R5': {'mask': df['granville_signal'] == 5, 'marker': 'v', 'color': 'red'},
        'R6': {'mask': df['granville_signal'] == 6, 'marker': 'v', 'color': 'orange'},
        'R7': {'mask': df['granville_signal'] == 7, 'marker': 'v', 'color': 'magenta'},
        'R8': {'mask': df['granville_signal'] == 8, 'marker': 'v', 'color': 'brown'},
    }

    addplots = []
    addplots.append(
        mpf.make_addplot(
            df[ma_col_name],
            color='orange',
            width=1,
            panel=0,
            label=f'MA{ma_window}'
        )
    )
    for label, rd in rule_defs.items():
        series = df['Close'].where(rd['mask'])
        if series.notna().any():
            addplots.append(
                mpf.make_addplot(
                    series,
                    type='scatter',
                    marker=rd['marker'],
                    markersize=100,
                    color=rd['color'],
                    panel=0,
                    label=label
                )
            )
    addplots.extend([
        mpf.make_addplot(df['Deviation'], panel=2, ylabel='Deviation(%)'),
        mpf.make_addplot(df['Slope'], panel=3, ylabel='Slope'),
        mpf.make_addplot(df[vol_ma_col_name], panel=4, ylabel=f'Vol MA{vol_ma_window}'),
    ])

    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=True,
        style='yahoo',
        title=f"Granville Rules - {stock_code}",
        addplot=addplots,
        panel_ratios=(3, 1, 1, 1, 1),
        figsize=(14, 10),
        returnfig=True
    )
    ax0 = axes[0]

    handles, labels = ax0.get_legend_handles_labels()
    ax0.legend(handles, labels, loc='upper left', ncol=4)

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return save_path

def plot_cross_chart(
    stock_code: int,
    start_date: str,
    end_date: str,
    db_config: dict,
    save_path: str = ".",
    short_window: int = 5,
    long_window: int = 20
) -> str:

    conn = get_db_connection(**db_config)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()

    if df.empty:
        print("查無資料")
        return {}

    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

    short_ma_col = f"MA{short_window}"
    long_ma_col = f"MA{long_window}"

    if short_ma_col not in df.columns:
        df = gt.moving_average(df, window=short_window, column='Close', out_col=short_ma_col)
    if long_ma_col not in df.columns:
        df = gt.moving_average(df, window=long_window, column='Close', out_col=long_ma_col)

    df = gt.crossover_signal(df, short_col=short_ma_col, long_col=long_ma_col, out_col='cross_signal')

    addplots = [
        mpf.make_addplot(df[short_ma_col], color='blue', width=1, panel=0, label=short_ma_col),
        mpf.make_addplot(df[long_ma_col], color='orange', width=1, panel=0, label=long_ma_col),
    ]

    golden_mask = df['cross_signal'] == 1
    death_mask = df['cross_signal'] == -1

    if golden_mask.any():
        addplots.append(
            mpf.make_addplot(
                df['Close'].where(golden_mask),
                type='scatter', marker='^', markersize=80,
                color='gold', panel=0, label='Golden Cross'
            )
        )
    if death_mask.any():
        addplots.append(
            mpf.make_addplot(
                df['Close'].where(death_mask),
                type='scatter', marker='v', markersize=80,
                color='black', panel=0, label='Death Cross'
            )
        )

    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=False,
        style='yahoo',
        title=f"{stock_code} — Cross Signals",
        addplot=addplots,
        panel_ratios=(3,),
        figsize=(12, 6),
        returnfig=True
    )
    ax = axes[0]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper left')

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return save_path

def plot_breakout_chart(
    stock_code: int,
    start_date: str,
    end_date: str,
    db_config: dict,
    save_path: str = ".",
    ma_window: int = 20
) -> dict:
    """
    從資料庫取 OHLCV 資料，畫出 K 線圖 + MA{ma_window}，並標記「突破／跌破」訊號。
    ma_window: 計算 MA 的時間週期
    最後存成 {save_prefix}_breakout.png。
    """
    conn = get_db_connection(**db_config)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()

    if df.empty:
        print("查無資料")
        return {}

    # 確保 index 為 DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

    ma_col_name = f"MA{ma_window}"
    if ma_col_name not in df.columns:
        df = gt.moving_average(df, window=ma_window, column='Close', out_col=ma_col_name)

    df = gt.breakout_signal(
        df,
        price_col='Close',
        ma_col=ma_col_name,
        out_col='breakout_signal'
    )

    addplots = [
        mpf.make_addplot(df[ma_col_name], color='orange', width=1, panel=0, label=ma_col_name)
    ]

    up_mask = df['breakout_signal'] == 1
    down_mask = df['breakout_signal'] == -1

    if up_mask.any():
        addplots.append(
            mpf.make_addplot(
                df['Close'].where(up_mask),
                type='scatter', marker='^', markersize=80,
                color='green', panel=0, label='Breakout Up'
            )
        )
    if down_mask.any():
        addplots.append(
            mpf.make_addplot(
                df['Close'].where(down_mask),
                type='scatter', marker='v', markersize=80,
                color='red', panel=0, label='Breakout Down'
            )
        )

    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=False,
        style='yahoo',
        title=f"{stock_code} — Breakout Signals",
        addplot=addplots,
        panel_ratios=(3,),
        figsize=(12, 6),
        returnfig=True
    )
    ax = axes[0]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper left')

    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

    return {"breakout_chart": save_path}



