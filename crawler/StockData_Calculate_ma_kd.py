from datetime import date
import pymssql
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

# ─── 日誌設定 ───────────────────────────────────────────────────
logging.basicConfig(
    filename='sp_scheduler_log.txt',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ─── MSSQL 連線參數 ───────────────────────────────────────────────────
db_settings = {
    "host":     "127.0.0.1",    # 或你的主機 IP / 主機名稱
    "user":     "110502025",        # 資料庫使用者
    "password": "1234",    # 資料庫密碼
    "database": "stock_database", # 你要連線的資料庫名稱
    "charset":  "utf8"
}

# 要處理的股票清單
STOCK_CODES = ["2330", "2454", "2317", "2308", "2382",
               "2891", "2881", "2882", "2303", "2412"]

# 建立 APScheduler 排程器
scheduler = BlockingScheduler(timezone='Asia/Taipei')


def call_stored_procedures():
    """
    依序呼叫 1) CalculateMA_All_Complete
           2) Calculate_KD_Values
    """
    conn = None
    try:
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()

        logging.info("開始執行 SP: CalculateMA_All_Complete")
        cursor.execute("EXEC dbo.CalculateMA_All_Complete")
        conn.commit()
        logging.info("完成 SP: CalculateMA_All_Complete")

        logging.info("開始執行 SP: Calculate_KD_Values")
        cursor.execute("EXEC dbo.Calculate_KD_Values")
        conn.commit()
        logging.info("完成 SP: Calculate_KD_Values")

    except Exception as e:
        logging.error(f"[ERROR] 呼叫 SP 過程發生錯誤：{e}")
    finally:
        if conn:
            conn.close()
            logging.info("資料庫連線已關閉")


def check_and_run_sp():
    """
    每天 14:05 執行：
      1) 檢查當天 stock_price_history_2023_to_2025 是否已有 10 支股票的資料
      2) 若筆數 >= 10，再呼叫儲存程序計算 MA 與 KD
      3) 否則在日誌記錄警告
    """
    today = date.today()
    conn = None

    try:
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()
        logging.info("開始執行 check_and_run_sp()")

        # 組合 IN 子句參數列表 (%s, %s, …)
        placeholders = ",".join(["%s"] * len(STOCK_CODES))
        sql = f"""
            SELECT COUNT(*)
            FROM dbo.stock_price_history_2023_to_2025
            WHERE [Date] = %s
              AND StockCode IN ({placeholders})
        """
        params = [today] + STOCK_CODES
        cursor.execute(sql, tuple(params))
        row = cursor.fetchone()
        count_today = row[0] if row else 0
        logging.info(f"今日 {today} 已插入歷史資料筆數：{count_today}")

        if count_today >= len(STOCK_CODES):
            logging.info(f"歷史資料齊全 ({count_today} 筆)，開始呼叫 MA/KD SP")
            call_stored_procedures()
        else:
            logging.warning(f"歷史資料不齊全 (僅 {count_today} 筆)，跳過 MA/KD 計算")

        logging.info("完成 check_and_run_sp")

    except Exception as e:
        logging.error(f"[ERROR] check_and_run_sp 發生例外：{e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_and_run_sp()
    '''
    # 只排程：每天 14:05 檢查並執行 MA/KD SP
    scheduler.add_job(
        check_and_run_sp,
        'cron',
        day_of_week='mon-fri',
        hour=14,
        minute=5,
        timezone='Asia/Taipei'
    )

    logging.info("排程設定完成：每日 14:05 執行 check_and_run_sp")
    print("啟動排程：每日 14:05 檢查並執行 MA/KD SP。")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("排程器停止")
    '''
