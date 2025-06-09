import time
import asyncio
import pandas as pd
from datetime import datetime
from core import analyze_stock, SignalConfig
from telegram.ext import Application
from utils.config import BOT_TOKEN, get_db_connection, db_cfg

CHECK_INTERVAL = 60  # 每幾秒檢查一次
SIGNAL_KEYWORDS = {"BUY", "SELL"}
processed_keys = set()

async def notify_users(message: str):
    app = Application.builder().token(BOT_TOKEN).build()
    bot = app.bot

    conn = get_db_connection(db_cfg)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM telegram_users")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"傳送失敗: {e}")

def get_latest_record():
    conn = get_db_connection(db_cfg)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 *
        FROM stock_price_realtime_2025
        ORDER BY [Date] DESC, [Time] DESC
    """)
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    # 手動轉成 dict
    columns = [column[0] for column in cursor.description]
    record = dict(zip(columns, row))

    conn.close()
    return record


def get_historical_data(stock_code: str, today: str) -> pd.DataFrame:
    conn = get_db_connection(db_cfg)
    query = """
            SELECT [Date] AS [date], [Open] AS [open], [High] AS [high], [Low] AS [low], [Close] AS [close], [Volume] AS [volume]
            FROM stock_price_history_2023_to_2025
            WHERE [StockCode] = ? AND [Date] <= ?
            ORDER BY [Date] ASC \
            """
    df = pd.read_sql_query(query, conn, params=[stock_code, today])
    conn.close()

    # 轉換欄位為 float
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)

    return df

def record_to_current_data(record):
    return {
        "price": record["Close"],
        "volume": record["Capacity"],
        "timestamp": datetime.strptime(f"{record['Date']} {record['Time']}", "%Y-%m-%d %H:%M:%S")
    }

def get_analysis_summary(response):
    if not response.success or not response.data.signals:
        return None, None
    last_signal = response.data.signals[-1]
    if last_signal.timestamp.date() != datetime.today().date():
        print(f"訊號日期為 {last_signal.timestamp.date()}，非今天日期，略過通知")
        return None, None

    summary = (
        f"建議交易訊號\n"
        f"股票代號: {response.data.stock_code}\n"
        f"葛蘭碧法則: {last_signal.rule_number}\n"
        f"建議操作: {last_signal.signal_type}\n"
        f"價格: {last_signal.price}\n"
        f"信心: {last_signal.confidence:.2f}\n"
        f"時間: {last_signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return last_signal.signal_type, summary

def log_signal_to_db(signal: dict, stock_code: str, notified: bool):
    conn = get_db_connection(db_cfg)
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO granville_signal_log (stock_code, signal_type, signal_time, price, confidence, notified)
                   VALUES (?, ?, ?, ?, ?, ?)
                   """, (
                       stock_code,
                       signal["signal_type"],
                       signal["timestamp"],
                       signal["price"],
                       signal["confidence"],
                       int(notified)
                   ))
    conn.commit()
    conn.close()

def get_watch_list() -> set:
    conn = get_db_connection(db_cfg)
    cursor = conn.cursor()
    cursor.execute("SELECT stock_code FROM watch_list")
    watch_list = {row[0] for row in cursor.fetchall()}
    conn.close()
    return watch_list

def main_loop():
    while True:
        record = get_latest_record()
        if not record:
            time.sleep(CHECK_INTERVAL)
            continue

        key = (record["Date"], record["Time"], record["StockCode"])
        if key in processed_keys:
            time.sleep(CHECK_INTERVAL)
            continue

        watch_list = get_watch_list()
        stock_code = record["StockCode"]
        if stock_code not in watch_list:
            print(f"股票 {stock_code} 不在 watch_list 中，略過分析")
            time.sleep(CHECK_INTERVAL)
            continue

        today_str = record["Date"].strftime("%Y-%m-%d")
        historical_df = get_historical_data(stock_code, today_str)
        current_data = record_to_current_data(record)
        config = SignalConfig(ma_period=20, enable_signal_filter=True)

        try:
            response = analyze_stock(
                stock_code=stock_code,
                historical_data=historical_df,
                current_data=current_data,
                config=config
            )
            print(response)

            last_signal_type, summary = get_analysis_summary(response)
            last_signal = response.data.signals[-1] if response.success and response.data.signals else None
            # 在處理分析結果之後
            if last_signal and last_signal_type and last_signal_type.upper() in SIGNAL_KEYWORDS:
                # 判斷是否為新訊號
                conn = get_db_connection(db_cfg)
                cursor = conn.cursor()
                cursor.execute("""
                               SELECT COUNT(*)
                               FROM granville_signal_log
                               WHERE stock_code = ?
                                 AND signal_type = ?
                                 AND signal_time = ?
                               """, (stock_code, last_signal.signal_type, last_signal.timestamp))
                exists = cursor.fetchone()[0]
                conn.close()

                if exists == 0:
                    # 發送通知
                    asyncio.run(notify_users(summary))
                    # 寫入資料庫
                    log_signal_to_db({
                        "signal_type": last_signal.signal_type,
                        "timestamp": last_signal.timestamp,
                        "price": last_signal.price,
                        "confidence": last_signal.confidence
                    }, stock_code, notified=True)
                else:
                    print(f"已發送過 {stock_code} {last_signal.signal_type} 於 {last_signal.timestamp}")
        except Exception as e:
            print(f"分析失敗: {e}")

        processed_keys.add(key)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
