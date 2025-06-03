from datetime import datetime, timedelta
from datetime import date
import pymssql
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import logging

# 設定 Log 檔案 (將訊息寫入 log 檔)
logging.basicConfig(
    filename='realtime_log.txt',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# MSSQL 設定
db_settings = {
    "host": "127.0.0.1",
    "user": "pohan",
    "password": "",
    "database": "ncu_database",
    "charset": "utf8"
}

# 建立排程器
scheduler = BlockingScheduler(timezone='Asia/Taipei')

# 記錄上次插入的股票數據
last_record = {}


def fetch_stock_data(stock_code, stock_type):
    """ 從 API 抓取指定股票的數據 """
    base_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_type}_{stock_code}.tw&json=1&delay=0"

    try:
        response = requests.get(base_url)
        response.raise_for_status()  # 檢查是否有 HTTP 錯誤
        data = response.json()

        if "msgArray" in data and len(data["msgArray"]) > 0:
            return data["msgArray"][0]  # 取得股票數據
        else:
            logging.warning(f"⚠️ {stock_code} 無資料回應 (API 正常但回傳空資料)")
    except Exception as e:
        logging.error(f"❌ 無法獲取 {stock_code} 的數據: {e}")

    return None


def parse_stock_data(stock_data):
    """ 解析 API 數據，並確保所有 `REAL` 類型數據為 float """

    def safe_float(value):
        """ 將字串轉換為浮點數，若為 '-' 則回傳 0.0 """
        try:
            return float(value.replace(',', '').replace('-', '0'))
        except ValueError:
            return 0.0

    latest_price = safe_float(stock_data.get("z", "0"))  # 最新成交價
    prev_close_price = safe_float(stock_data.get("y", "0"))  # 昨日收盤價
    price_change = latest_price - prev_close_price if latest_price != 0 else 0.0  # 只在有數據時計算

    return {
        "trade_time": stock_data.get("t", "00:00:00"),  # 交易時間
        "trade_volume": int(stock_data.get("tv", "0").replace("-", "0")),  # 成交股數
        "latest_price": latest_price,  # 最新成交價
        "high_price": safe_float(stock_data.get("h", "0")),  # 最高價
        "low_price": safe_float(stock_data.get("l", "0")),  # 最低價
        "open_price": safe_float(stock_data.get("o", "0")),  # 開盤價
        "price_change": price_change,  # 漲跌價差
        "trade_value": 0,  # 成交金額 (API 無提供，手動設為 0)
        "trade_count": 0  # 成交筆數 (API 無提供，手動設為 0)
    }


def daily_crawler():
    """ 每次偵測股票變動，只有數據變動時才寫入資料庫 """
    stock_list = [
        {"stock_code": "2330", "stock_name": "台積", "stock_type": "tse"},
        {"stock_code": "2454", "stock_name": "聯發", "stock_type": "tse"},
        {"stock_code": "2317", "stock_name": "鴻海", "stock_type": "tse"},
        {"stock_code": "2308", "stock_name": "台達電", "stock_type": "tse"},
        {"stock_code": "2382", "stock_name": "廣達", "stock_type": "tse"},
        {"stock_code": "2891", "stock_name": "中信金", "stock_type": "tse"},
        {"stock_code": "2881", "stock_name": "富邦金", "stock_type": "tse"},
        {"stock_code": "2882", "stock_name": "國泰", "stock_type": "tse"},
        {"stock_code": "2303", "stock_name": "聯電", "stock_type": "tse"},
        {"stock_code": "2412", "stock_name": "中華電", "stock_type": "tse"}
    ]

    conn = pymssql.connect(**db_settings)
    cursor = conn.cursor()

    today = datetime.today().strftime('%Y-%m-%d')

    for stock in stock_list:
        stock_code = stock["stock_code"]
        stock_name = stock["stock_name"]
        stock_type = stock["stock_type"]

        # 取得 API 數據
        stock_data = fetch_stock_data(stock_code, stock_type)
        if not stock_data:
            logging.warning(f"⚠️ {stock_name}({stock_code}) 無法獲取數據，跳過")
            continue

        # 解析數據
        parsed_data = parse_stock_data(stock_data)

        # 構造新數據
        new_record = (
            today,                        #[Date]
            parsed_data["trade_time"],    #[Time]
            stock_code,                   #[StockCode]
            parsed_data["trade_volume"],  #[Capacity]
            parsed_data["trade_value"],   #[Volume]
            parsed_data["open_price"],    #[Open]
            parsed_data["high_price"],    #[High]
            parsed_data["low_price"],     #[Low]
            parsed_data["latest_price"],  #[Close]
            parsed_data["price_change"],  #[Change]
            parsed_data["trade_count"]    #[Transaction]
        )

        # 檢查是否與上次相同
        prev_record = last_record.get(stock_code, None)
        if prev_record and prev_record == new_record:
            logging.info(f"🔄 {stock_name}({stock_code}) 數據未變動，跳過")
            continue  # 如果沒有變化，跳過寫入資料庫

        # 更新記錄
        last_record[stock_code] = new_record

        # **將資料寫入資料庫**
        try:
            cursor.execute("""
                INSERT INTO stock_price_realtime_2025
                ([Date], [Time], [StockCode], [Capacity], [Volume],
                 [Open], [High], [Low], [Close], [Change], [Transaction])
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, new_record)
            conn.commit()
            logging.info(f"✅ 成功寫入資料: {stock_name}({stock_code})")
        except Exception as e:
            logging.error(f"❌ 無法將 {stock_code} 資料寫入資料庫: {e}")

    conn.close()


# 讓 Schedular 在設定的時間可以正常關閉
def end_program():
    logging.info("✅ Program ends. Scheduler 停止運行")
    scheduler.shutdown(wait=False)  # 直接關閉 Scheduler

def clear_realtime():
    """在每日開盤時，清空當天的 realtime 表，並重置 last_record"""
    global last_record
    conn = pymssql.connect(**db_settings)
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE stock_price_realtime_2025")
        conn.commit()
        last_record.clear()
        logging.info("🧹 stock_price_realtime_2025 已清空，開始新一日記錄")
    except Exception as e:
        logging.error(f"❌ 清空 stock_price_realtime_2025 失敗: {e}")
    finally:
        conn.close()



def fetch_and_save_today_history():
    """收盤後跑一次：抓今天的 STCK_DAY API 並寫入 stock_price_history_2023_to_2025"""
    stock_codes = ["2330","2454","2317","2308","2382",
                   "2891","2881","2882","2303","2412"]
    today = date.today()
    date_str = today.strftime('%Y%m%d')   # 20250530
    conn = pymssql.connect(**db_settings)
    cursor = conn.cursor()

    for code in stock_codes:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={code}"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            js = resp.json()
            if js.get('stat') != 'OK':
                logging.warning(f"⚠️ {code} STΚ_DAY API 回傳 stat={js.get('stat')}")
                continue

            # 找出當天那一筆
            for row in js['data']:
                y, m, d = row[0].split('/')
                y = int(y) + 1911
                # row_date = date(y, int(m), int(d))
                formatted_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                formatted_date = datetime.strptime(formatted_date, '%Y-%m-%d').date()
                # if row_date != today:
                if formatted_date != today:
                    continue

                # safe 轉型
                def sf(v):
                    return float(v.replace(',','').replace('X','0')) if v.strip() else 0.0

                entry = (
                    # row_date,     # Date
                    formatted_date,
                    code,         # StockCode
                    int(row[1].replace(',','')),   # Capacity
                    float(row[2].replace(',','')), # Volume
                    sf(row[3]),   # Open
                    sf(row[4]),   # High
                    sf(row[5]),   # Low
                    sf(row[6]),   # Close
                    sf(row[7]),   # Change
                    int(row[8].replace(',',''))    # Transaction
                )

                # 避免重覆寫入
                cursor.execute("""
                    IF NOT EXISTS(
                      SELECT 1 FROM dbo.stock_price_history_2023_to_2025
                      WHERE [Date]=%s AND [StockCode]=%s
                    )
                    INSERT INTO dbo.stock_price_history_2023_to_2025
                    ([Date],[StockCode],[Capacity],[Volume],[Open],[High],
                     [Low],[Close],[Change],[Transaction])
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, entry[:2] + entry)
                conn.commit()
                # logging.info(f"✅ {code}({row_date}) 寫入 stock_price_history")
                logging.info(f"✅ {code}({formatted_date}) 寫入 stock_price_history")
                break

        except Exception as e:
            logging.error(f"❌ {code} 歷史資料寫入失敗：{e}")

    conn.close()









#### main ######################################

# 檢查當天是否為交易日
conn = pymssql.connect(**db_settings)
with conn.cursor() as cursor:
    today = datetime.today().strftime('%Y-%m-%d')
    command = f"SELECT * FROM [dbo].[calendar] WHERE date = '{today}'"
    cursor.execute(command)
    result = cursor.fetchone()
conn.commit()
conn.close()

# 如果當天不休市，則開始排程
if result and result[1] != -1:
    # scheduler.add_job(daily_crawler, 'interval', minutes=1)    ## 1分鐘執行一次
    #
    # run_time = datetime.now() + timedelta(minutes=1)
    # scheduler.add_job(end_program, 'date', run_date=run_time)

    # 1) 每日 09:00 清空 realtime 表
    scheduler.add_job(
        clear_realtime,
        'cron',
        day_of_week='mon-fri',
        hour=8,
        minute=58,
        timezone='Asia/Taipei'
    )

    # 2) 每分鐘執行一次爬蟲
    # 只在每周一到周五、09:00–12:59 以及 13:00–13:30 之間，每分鐘呼叫一次 daily_crawler
    scheduler.add_job(
        daily_crawler,
        'cron',
        day_of_week='mon-fri',
        hour='9-12',
        minute='*',
        timezone='Asia/Taipei'
    )
    scheduler.add_job(
        daily_crawler,
        'cron',
        day_of_week='mon-fri',
        hour='13',
        minute='0-30',
        timezone='Asia/Taipei'
    )

    # 不再需要 end_program，也不用 scheduler.shutdown()

    # 3) 每個交易日 14:00 執行一次寫入history資訊
    scheduler.add_job(
        fetch_and_save_today_history,
        'cron',
        day_of_week='mon-fri',
        hour=14, minute=0,
        timezone='Asia/Taipei'
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.info("❗ Program stopped by user.")
else:
    logging.info("⛔ 今天休市，程式結束。")
