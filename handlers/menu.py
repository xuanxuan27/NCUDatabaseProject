from telegram import Update
from telegram.ext import ContextTypes
from handlers.watch_list import start_watchlist, show_watchlist
from utils.keyboards import markup, chart_markup
from utils.config import get_db_connection, db_cfg
import logging
import asyncio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 存 chat_id
    def store_chat_id():
        conn = get_db_connection(db_cfg)
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM telegram_users WHERE user_id = ?)
                INSERT INTO telegram_users (user_id, chat_id, username)
                VALUES (?, ?, ?)
            ELSE
                UPDATE telegram_users SET chat_id = ?, username = ? WHERE user_id = ?
        """, (user.id, user.id, chat_id, user.username, chat_id, user.username, user.id))
        conn.commit()
        conn.close()

    await asyncio.get_running_loop().run_in_executor(None, store_chat_id)

    await update.message.reply_text(
        "歡迎使用股票視界，請從下方選單中選擇功能：",
        reply_markup=markup
    )
    return 0

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    logging.info(f"{user.username} 選擇了功能：{text}")

    if text == "查詢股價資料":
        await update.message.reply_text("請輸入股票代碼，例如：2330(輸入0結束查詢)")
        return 1
    elif text == "顯示圖表":
        await update.message.reply_text("請選擇要輸出的股票圖表類型：", reply_markup=chart_markup)
        return 101
    elif text == "輸入/移除追蹤標的清單":
        return await start_watchlist(update, context)
    elif text == "追蹤標的清單":
        return await show_watchlist(update, context)
    elif text == "回測":
        await update.message.reply_text("請輸入回測參數")
    else:
        await update.message.reply_text("請從選單中選擇有效的選項")
        return 0
