# plot_granville.py
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np

from data_access import get_db_connection, fetch_stock_data
from db_config import db_cfg

# 1. 中文字型設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_granville_charts(
    stock_code: int,
    start_date: str,
    end_date: str,
    db_config: dict,
    save_prefix: str = "granville"
) -> dict:
    """
    繪製依 Granville 八條法則的綜合圖：
      - Panel0: K 線 + MA20
      - Panel1: 成交量
      - Panel2: 價格/MA20 偏離率
      - Panel3: MA20 斜率
      - Panel4: 成交量 MA5
    並用不同顏色三角形代表 R1–R8，標示於圖例中。

    回傳每個圖檔路徑。
    """
    # 連線並取資料
    conn = get_db_connection(**db_config)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()
    if df.empty:
        print("查無資料")
        return {}

    # 計算輔助指標
    df['Deviation'] = (df['Close'] - df['MA20']) / df['MA20'] * 100
    df['Slope']     = df['MA20'].diff()
    df['Vol_MA5']   = df['Volume'].rolling(5).mean()

    # 準備各規則的散點
    rule_defs = {
        'R1': {'mask': df['buy_or_sell']=='Buy_GranvilleRule1', 'marker':'^', 'color':'green'},
        'R2': {'mask': df['buy_or_sell']=='Buy_GranvilleRule2', 'marker':'^', 'color':'blue'},
        'R3': {'mask': df['buy_or_sell']=='Buy_GranvilleRule3', 'marker':'^', 'color':'purple'},
        'R4': {'mask': df['buy_or_sell']=='Buy_GranvilleRule4', 'marker':'^', 'color':'cyan'},
        'R5': {'mask': df['buy_or_sell']=='Sell_GranvilleRule5', 'marker':'v', 'color':'red'},
        'R6': {'mask': df['buy_or_sell']=='Sell_GranvilleRule6', 'marker':'v', 'color':'orange'},
        'R7': {'mask': df['buy_or_sell']=='Sell_GranvilleRule7', 'marker':'v', 'color':'magenta'},
        'R8': {'mask': df['buy_or_sell']=='Sell_GranvilleRule8', 'marker':'v', 'color':'brown'},
    }

    # 建立 addplot 列表
    addplots = []
    # MA20
    addplots.append(mpf.make_addplot(df['MA20'], color='orange', width=1, panel=0, ylabel='MA20'))
    # 各 rule 的 scatter
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
    # Deviation, Slope, Vol_MA5
    addplots.extend([
        mpf.make_addplot(df['Deviation'], panel=2, ylabel='Deviation(%)'),
        mpf.make_addplot(df['Slope'],     panel=3, ylabel='Slope'),
        mpf.make_addplot(df['Vol_MA5'],   panel=4, ylabel='Vol MA5'),
    ])

    # 畫圖
    fig, axes = mpf.plot(
        df,
        type='candle',
        volume=True,
        style='yahoo',
        title=f"Granville Rules - {stock_code}",
        addplot=addplots,
        panel_ratios=(3,1,1,1,1),
        figsize=(14,10),
        returnfig=True
    )
    ax0 = axes[0]

    # 顯示 legend (包含 R1–R8)
    handles, labels = ax0.get_legend_handles_labels()
    ax0.legend(handles, labels, loc='upper left', ncol=4)

    # 存檔並返回
    paths = {}
    out = f"{save_prefix}_granville_chart.png"
    fig.savefig(out, bbox_inches='tight')
    plt.close(fig)
    paths['granville'] = out
    return paths


if __name__ == "__main__":
    
    stock_code = 2317
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    result = plot_granville_charts(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        db_config=db_cfg,
        save_prefix=f"images/{stock_code}"
    )
    print(result)
