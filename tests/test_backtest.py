# plot/example_usage.py

from data_access import get_db_connection, fetch_stock_data, db_cfg
from backtest.backtest import prepare_signals, backtest_single_stock_enhanced

def main():
    stock_code = 2317
    start_date = '2023-01-01'
    end_date   = '2023-06-30'

    # 1. 讀取原始股價資料
    conn = get_db_connection(**db_cfg)
    df = fetch_stock_data(conn, stock_code, start_date, end_date)
    conn.close()

    # 2. 計算訊號欄位
    df = prepare_signals(df)

    # 3. 執行回測，取回 summary dict
    summary = backtest_single_stock_enhanced(
        df=df,
        stock_id=str(stock_code),
        take_profit_pct=0.1,
        initial_capital=1_000_000
    )

    # 4. 印出「回測結果摘要」
    print("=== 回測結果摘要 ===")
    print(f"起始資金：{summary['起始資金']:.2f}")
    print(f"最終資產：{summary['最終資產']:.2f}")
    print(f"報酬率：{summary['報酬率']:.2f}%\n")

    # 5. 印出「最終持倉狀況」
    pos = summary['最終持倉']
    print("=== 最終持倉狀況 ===")
    print(f"股票代號：{pos['股票代號']}")
    print(f"持有股數：{pos['持有股數']}")
    print(f"最新收盤：{pos['最新收盤']:.2f}")
    print(f"持倉市值：{pos['持倉市值']:.2f}\n")

    # 6. 印出「交易歷史」表
    print("=== 交易歷史 ===")
    hist_df = summary['交易歷史']
    if hist_df.empty:
        print("沒有交易紀錄。")
    else:
        print(hist_df.to_string(index=False))

    # 7. 印出「策略總結表」
    print("\n=== 策略總結表 ===")
    summ_df = summary['策略總結表']
    print(summ_df.to_string(index=False))

if __name__ == "__main__":
    main()
