# example_usage.py

"""
範例：如何使用 plot 套件來生成各種技術分析圖表
"""

from plot import (
    get_db_connection,
    fetch_stock_data,
    plot_all_charts,
    plot_granville_charts,
    plot_cross_chart,
    plot_breakout_chart
)
from plot.db_config import db_cfg

def main():
    stock_code = 2317
    start_date = '2023-01-01'
    end_date = '2023-06-30'
    output_dir = f"plot/images/{stock_code}"

    # 1. 生成一般圖表（K線、布林帶、RSI、KD），並包含 Granville 註記
    charts = plot_all_charts(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        output_prefix=output_dir,
        db_config=db_cfg,
        bollinger_window=20,
        rsi_period=14,
        kd_k_period=14,
        kd_d_period=3
    )
    for name, path in charts.items():
        print(f"{name} chart saved at: {path}")

    # 2. 生成 Granville 綜合圖表（包含八條法則標註）
    granville_result = plot_granville_charts(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        db_config=db_cfg,
        save_prefix=output_dir,
        ma_window=20,
        vol_ma_window=5
    )
    print(f"Granville chart saved at: {granville_result.get('granville')}")

    # 3. 生成黃金交叉／死亡交叉圖，指定短期 MA5、長期 MA20
    cross_path = plot_cross_chart(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        output_prefix=output_dir,
        db_config=db_cfg,
        short_window=5,
        long_window=20
    )
    print(f"Cross chart saved at: {cross_path}")

    # 4. 生成價格突破／跌破圖，指定 MA20
    breakout_path = plot_breakout_chart(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        output_prefix=output_dir,
        db_config=db_cfg,
        ma_window=20
    )
    print(f"Breakout chart saved at: {breakout_path}")

if __name__ == "__main__":
    main()
