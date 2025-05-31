import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import matplotlib.dates as mdates

from data_access import get_db_connection, fetch_stock_data
from db_config import db_cfg

# 1. 中文字型設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_candle_and_volume_chart(
    df: pd.DataFrame,
    stock_code: int,
    save_path: str = "chart.png"
) -> str:
    """
    繪製 K 棒＋成交量＋MA＋買賣訊號，並存檔。
    """
    # 買賣訊號
    buy_mask  = df['buy_or_sell'].str.startswith('Buy_GranvilleRule',  na=False)
    sell_mask = df['buy_or_sell'].str.startswith('Sell_GranvilleRule', na=False)
    buy_sig   = np.where(buy_mask,   df['Close'], np.nan)
    sell_sig  = np.where(sell_mask,  df['Close'], np.nan)

    # addplot
    addplots = []
    for col, color in [('MA5','blue'), ('MA20','orange'), ('MA60','green')]:
        if df[col].notna().any():
            addplots.append(mpf.make_addplot(df[col], color=color, width=1, label=col))
    if buy_mask.any():
        addplots.append(mpf.make_addplot(buy_sig, type='scatter', marker='^', markersize=80, color='green', label='Buy'))
    if sell_mask.any():
        addplots.append(mpf.make_addplot(sell_sig, type='scatter', marker='v', markersize=80, color='red', label='Sell'))

    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=True,
        title=str(stock_code),
        addplot=addplots,
        style='yahoo',
        panel_ratios=(3,1),
        figsize=(12, 8),
        returnfig=True
    )
    ax = axes[0]

    # 註記 R#
    for dt, row in df[df['buy_or_sell'].str.contains('GranvilleRule', na=False)].iterrows():
        rule_no = row['buy_or_sell'].split('GranvilleRule')[-1]
        price   = row['Close']
        is_buy  = row['buy_or_sell'].startswith('Buy')
        offset  = 10 if is_buy else -10
        ax.annotate(
            f'R{rule_no}', xy=(dt, price), xytext=(0, offset), textcoords='offset points',
            ha='center', va='bottom' if is_buy else 'top',
            color='green' if is_buy else 'red', fontsize=9, clip_on=False
        )

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper left')
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_bollinger(df: pd.DataFrame, window: int = 20, num_std: int = 2, save_path: str = None):
    ma    = df['Close'].rolling(window).mean()
    std   = df['Close'].rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std

    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df.index, df['Close'], label='Close')
    ax.plot(df.index, ma, label=f'MA{window}')
    ax.plot(df.index, upper, label='Upper Band')
    ax.plot(df.index, lower, label='Lower Band')
    ax.set_title('Bollinger Bands')
    ax.legend()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_rsi(df: pd.DataFrame, period: int = 14, save_path: str = None):
    delta    = df['Close'].diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs       = avg_gain / avg_loss
    rsi      = 100 - 100 / (1 + rs)

    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(df.index, rsi, label='RSI')
    ax.axhline(70, linestyle='--', label='Overbought')
    ax.axhline(30, linestyle='--', label='Oversold')
    ax.set_title('Relative Strength Index')
    ax.legend()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_kd(df: pd.DataFrame, k_period: int = 14, d_period: int = 3, save_path: str = None):
    low_min  = df['Low'].rolling(k_period).min()
    high_max = df['High'].rolling(k_period).max()
    rsv      = (df['Close'] - low_min) / (high_max - low_min) * 100

    k = rsv.ewm(span=d_period, adjust=False).mean()
    d = k.ewm(span=d_period, adjust=False).mean()

    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(df.index, k, label='%K')
    ax.plot(df.index, d, label='%D')
    ax.set_title('Stochastic Oscillator (KD)')
    ax.legend()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_all_charts(
    stock_code: int,
    start_date: str,
    end_date: str,
    output_prefix: str,
    db_config: dict
) -> dict:
    """
    依序生成 K 線圖、布林帶、RSI、KD 圖，回傳各檔案路徑。
    """
    conn = get_db_connection(**db_config)
    df   = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()

    if df.empty:
        print("查無資料")
        return {}

    results = {}
    # K 線與成交量
    results['candle'] = plot_candle_and_volume_chart(df, stock_code, f"{output_prefix}_candle.png")
    # Bollinger
    results['bollinger'] = plot_bollinger(df, save_path=f"{output_prefix}_bollinger.png")
    # RSI
    results['rsi'] = plot_rsi(df, save_path=f"{output_prefix}_rsi.png")
    # KD
    results['kd']  = plot_kd(df, save_path=f"{output_prefix}_kd.png")

    return results


if __name__ == "__main__":
    stock_code = 2317
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    outputs = plot_all_charts(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        output_prefix=f"images/{stock_code}",
        db_config=db_cfg
    )
    for name, path in outputs.items():
        print(f"{name} chart saved at {path}")