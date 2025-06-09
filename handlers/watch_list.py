import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.config import db_cfg, get_db_connection
from utils.keyboards import markup

async def start_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "請輸入 '+股票代碼' 加入追蹤，'-股票代碼' 移除追蹤，輸入 0 結束。"
    )
    return 20


async def handle_watchlist_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "0":
        await update.message.reply_text("追蹤標的清單操作結束。", reply_markup=markup)
        return 0

    if text.startswith("+"):
        stock_code = text[1:]

        def add_stock():
            conn = get_db_connection(db_cfg)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT 1 FROM watch_list WHERE stock_code = ?", (stock_code,))
                exists = cursor.fetchone() is not None
                if not exists:
                    cursor.execute(
                        "INSERT INTO watch_list (stock_code, add_time) VALUES (?, GETDATE())",
                        (stock_code,)
                    )
                    conn.commit()
                return not exists  # True if newly added
            finally:
                conn.close()

        added = await asyncio.get_running_loop().run_in_executor(None, add_stock)
        if added:
            await update.message.reply_text(f"✅ 已新增追蹤標的：{stock_code}")
        else:
            await update.message.reply_text(f"⚠️ {stock_code} 已經在追蹤清單中。")

    elif text.startswith("-"):
        stock_code = text[1:]

        def remove_stock():
            conn = get_db_connection(db_cfg)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watch_list WHERE stock_code = ?", (stock_code,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected

        affected = await asyncio.get_running_loop().run_in_executor(None, remove_stock)
        if affected:
            await update.message.reply_text(f"已移除追蹤標的：{stock_code}")
        else:
            await update.message.reply_text(f"{stock_code} 不在追蹤清單中。")

    else:
        await update.message.reply_text("格式錯誤，請輸入 '+股票代碼' 或 '-股票代碼'，輸入 0 結束。")

    return 20

async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def fetch_stocks():
        conn = get_db_connection(db_cfg)
        cursor = conn.cursor()
        cursor.execute("SELECT stock_code FROM watch_list ORDER BY add_time DESC")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    stock_list = await asyncio.get_running_loop().run_in_executor(None, fetch_stocks)

    if stock_list:
        text = "您目前追蹤的股票有：\n" + "\n".join(stock_list)
    else:
        text = "您目前沒有追蹤任何股票。"

    await update.message.reply_text(text, reply_markup=markup)

    return 0