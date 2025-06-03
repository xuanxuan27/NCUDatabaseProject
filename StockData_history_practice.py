import requests
import pymssql
import concurrent.futures
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 資料庫設定
db_settings = {
    "host": "127.0.0.1",
    "user": "pohan",
    "password": "",
    "database": "ncu_database",
    "charset": "utf8"
}

# 建立資料表的函數
def create_table():
    try:
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()
        cursor.execute("""
            IF OBJECT_ID('stock_price_history_2023_to_2025', 'U') IS NOT NULL
                DROP TABLE stock_price_history_2023_to_2025;
            CREATE TABLE stock_price_history_2023_to_2025 (
                [Date]       DATE,
                [StockCode]  VARCHAR(10),
                [Capacity]   BIGINT,
                [Volume]     BIGINT,
                [Open]       FLOAT,
                [High]       FLOAT,
                [Low]        FLOAT,
                [Close]      FLOAT,
                [Change]     FLOAT,
                [Transaction] BIGINT,
                [MA5]        FLOAT,
                [MA10]       FLOAT,
                [MA20]       FLOAT,
                [MA60]       FLOAT,
                [MA120]      FLOAT,
                [MA240]      FLOAT,
                [K_value]    FLOAT,
                [D_value]    FLOAT
            );
        """)
        conn.commit()
        print("成功建立資料表：stock_price_history_2023_to_2025")
    except Exception as e:
        print(f"資料表建立失敗：{e}")
    finally:
        conn.close()

# 儲存資料的函數
def save_to_db(data):
    try:
        conn = pymssql.connect(**db_settings)
        cursor = conn.cursor()
        for row in data:
            cursor.execute(
                """
                INSERT INTO stock_price_history_2023_to_2025
                ([Date], [StockCode], [Capacity], [Volume],
                 [Open], [High], [Low], [Close],
                 [Change], [Transaction],
                 [MA5], [MA10], [MA20],
                 [MA60], [MA120], [MA240],
                 [K_value], [D_value])
                VALUES
                (%s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s,
                 NULL, NULL, NULL,
                 NULL, NULL, NULL,
                 NULL, NULL)
                """, row
            )
        conn.commit()
        print(f"成功儲存 {len(data)} 筆資料")
    except Exception as e:
        print(f"資料庫錯誤：{e}")
    finally:
        conn.close()

# 下載上市資料
def fetch_twse_data(stock_code, start_date, end_date):
    all_data = []
    # 從起始月的第一天開始
    current_date = start_date.replace(day=1)

    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_code}"
        print(f"正在取得 {stock_code} 的資料 (日期: {date_str})...")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['stat'] == "OK":
                for row in data['data']:
                    try:
                        # 修正日期轉換問題
                        year, month, day = row[0].split('/')
                        year = int(year) + 1911
                        formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        formatted_date = datetime.strptime(formatted_date, '%Y-%m-%d').date()

                        def safe_float(value):
                            try:
                                return float(value.replace(',', '').replace('X', '0'))
                            except ValueError:
                                return 0.0

                        entry = (
                            formatted_date, stock_code,
                            int(row[1].replace(',', '')),
                            int(row[2].replace(',', '')),
                            safe_float(row[3]),
                            safe_float(row[4]),
                            safe_float(row[5]),
                            safe_float(row[6]),
                            safe_float(row[7]) if row[7].strip() else 0,
                            int(row[8].replace(',', ''))
                        )
                        all_data.append(entry)
                    except Exception as e:
                        print(f"日期轉換失敗於 {stock_code}：{e}")
        except Exception as e:
            print(f"{stock_code} 的資料取得失敗：{e}")

        # 下一輪直接跳到「下個月」的同一天（因為 day=1，所以永遠是下月 1 號）
        current_date += relativedelta(months=1)
        time.sleep(1)  # 避免 API 過載

    if all_data:
        save_to_db(all_data)

# 台灣 50 前 10 大成分股
def main():
    create_table()

    stock_list = [
        "2330", "2454", "2317", "2308", "2382",
        "2891", "2881", "2882", "2303", "2412"
    ]

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 5, 30)
    # end_date = datetime.today()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_twse_data, stock, start_date, end_date)
            for stock in stock_list
        ]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                print(f"完成：{result}")
            else:
                print("無資料")

if __name__ == "__main__":
    main()



#
# SELECT *  FROM [ncu_database].[dbo].[stock_price_history_2023_to_2025]
# ORDER BY date ASC, StockCode ASC;