from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging

reply_keyboard = [['查詢股價資料', '顯示圖表'],
                  ['輸入/移除追蹤標的清單', '追蹤標的清單'],
                  ['回測']]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

chart_keyboard = [
    ['K線圖', '布林通道'],
    ['相對強弱指標 (RSI)', 'KD 指標'],
    ['葛蘭碧法則', '交叉訊號'],
    ['突破訊號', '結束']
]
chart_markup = ReplyKeyboardMarkup(chart_keyboard, one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logging.info(f"收到 /start 指令，來自使用者: {user.username} ({user.id})")
    await update.message.reply_text(
        text="歡迎使用股票視界，請從下方選單中選擇功能：",
        reply_markup=markup
    )

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
    elif text == "回測":
        await update.message.reply_text("請輸入回測參數")
    elif text == "結束":
        await update.message.reply_text("感謝使用股票視界！")
    else:
        await update.message.reply_text("請從選單中選擇有效的選項")