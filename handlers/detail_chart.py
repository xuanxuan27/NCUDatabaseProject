import logging
import re
import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from utils.config import db_cfg, get_db_connection
from utils.keyboards import markup
from plot import (
    fetch_stock_data,
    plot_candle_and_volume_chart,
    plot_bollinger,
    plot_rsi,
    plot_kd,
    plot_granville_charts,
    plot_cross_chart,
    plot_breakout_chart,
)

WAITING_FOR_CHART_TYPE = 101  # 顯示圖表：第一步選圖類型
WAITING_FOR_STOCK_CODE_CHART = 102  # 顯示圖表：輸入股票代碼
WAITING_FOR_DATE_RANGE = 103

async def handle_chart_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chart_type = update.message.text
    logging.info(f"使用者選擇圖表類型：{chart_type}")

    if chart_type == "結束":
        await update.message.reply_text("已結束，回到主選單。", reply_markup=markup)
        return 0
    else:
        context.user_data['chart_type'] = chart_type
        await update.message.reply_text("請輸入股票代碼，例如：2330")
        return WAITING_FOR_STOCK_CODE_CHART

async def handle_stock_code_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock_code = update.message.text
    context.user_data['stock_code'] = stock_code
    await update.message.reply_text("請輸入查詢的日期範圍，格式如：20240101/20240601")
    return WAITING_FOR_DATE_RANGE

async def handle_date_range_and_generate_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_range = update.message.text.strip()
    match = re.match(r'(\d{8})\s*/\s*(\d{8})', date_range)

    if not match:
        await update.message.reply_text("日期格式錯誤，請重新輸入，例如：20240101/20240601")
        return WAITING_FOR_DATE_RANGE

    start_date_raw, end_date_raw = match.groups()
    # 把 20240101 轉成 2024-01-01 格式，方便後續處理
    start_date = f"{start_date_raw[:4]}-{start_date_raw[4:6]}-{start_date_raw[6:]}"
    end_date = f"{end_date_raw[:4]}-{end_date_raw[4:6]}-{end_date_raw[6:]}"

    stock_code = context.user_data.get('stock_code')
    chart_type = context.user_data.get('chart_type')

    try:
        conn = get_db_connection(db_cfg)
        df = fetch_stock_data(conn, stock_code, start_date, end_date)
    except Exception as e:
        await update.message.reply_text(f"⚠️ 取得資料失敗：{e}")
        return 0

    img_dir = "images"
    os.makedirs(img_dir, exist_ok=True)
    save_prefix = f"{stock_code}_{chart_type.replace(' ', '_')}"
    out_file = f"{save_prefix}.png"
    save_path = os.path.join(img_dir, out_file)
    print(save_path)

    try:
        if chart_type == 'K線圖':
            ret = plot_candle_and_volume_chart(df, stock_code, save_path=save_path)
        elif chart_type == '布林通道':
            ret = plot_bollinger(df, save_path=save_path)
        elif chart_type == '相對強弱指標 (RSI)':
            ret = plot_rsi(df, save_path=save_path)
        elif chart_type == 'KD 指標':
            ret = plot_kd(df, save_path=save_path)
        elif chart_type == '葛蘭碧法則':
            ret = plot_granville_charts(stock_code, start_date, end_date, db_cfg, save_path=save_path)
        elif chart_type == '交叉訊號':
            ret = plot_cross_chart(stock_code, start_date, end_date, db_cfg, save_path=save_path)
        elif chart_type == '突破訊號':
            ret = plot_breakout_chart(stock_code, start_date, end_date, db_cfg, save_path=save_path)
        else:
            await update.message.reply_text("未知的圖表類型，請重新開始")
            return ConversationHandler.END

        if isinstance(ret, dict):
            img_file = list(ret.values())[0]
        elif isinstance(ret, str):
            img_file = ret
        else:
            await update.message.reply_text("繪圖函式沒有回傳有效檔案路徑")
            return WAITING_FOR_CHART_TYPE

        with open(img_file, 'rb') as f:
            await update.message.reply_photo(photo=f)

    except Exception as e:
        await update.message.reply_text(f"⚠️ 繪圖失敗：{e}")

    context.user_data.clear()
    return WAITING_FOR_CHART_TYPE