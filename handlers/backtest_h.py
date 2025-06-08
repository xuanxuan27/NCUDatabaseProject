from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import pandas as pd
import backtest.backtest as backtest
from utils.config import db_cfg, get_db_connection

WAITING_FOR_STOCK_CODE_b = 301
WAITING_FOR_TAKE_PROFIT = 302
WAITING_FOR_INITIAL_CAPITAL = 303

def fetch_stock_data(stock_code: str) -> pd.DataFrame:
    query = """
    SELECT * FROM stock_price_history_2023_to_2025
    WHERE StockCode = ?
    ORDER BY [Date] ASC
    """
    try:
        with get_db_connection(db_cfg) as conn:
            df = pd.read_sql(query, conn, params=[stock_code])
        return df
    except Exception as e:
        print(f"資料庫查詢錯誤: {e}")
        return pd.DataFrame()

async def receive_stock_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock_code = update.message.text.strip()
    context.user_data["stock_code"] = stock_code
    await update.message.reply_text("請輸入停利百分比（小數），例如：0.1 表示10%")
    return WAITING_FOR_TAKE_PROFIT

async def receive_take_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        take_profit = float(text)
    except ValueError:
        await update.message.reply_text("請輸入有效的數字，例如 0.1")
        return WAITING_FOR_TAKE_PROFIT

    context.user_data["take_profit_pct"] = take_profit
    await update.message.reply_text("請輸入初始資金（數字）")
    return WAITING_FOR_INITIAL_CAPITAL

async def receive_initial_capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "":
        initial_capital = 1_000_000
    else:
        try:
            initial_capital = float(text)
        except ValueError:
            await update.message.reply_text("請輸入有效的數字")
            return WAITING_FOR_INITIAL_CAPITAL

    context.user_data["initial_capital"] = initial_capital

    stock_code = context.user_data["stock_code"]
    take_profit_pct = context.user_data["take_profit_pct"]

    # 取得股票資料
    df = fetch_stock_data(stock_code)
    if df is None or df.empty:
        await update.message.reply_text("找不到該股票資料，請重新開始回測流程。")
        return ConversationHandler.END

    df = backtest.prepare_signals(df)
    summary = backtest.backtest_single_stock_enhanced(
        df,
        stock_code,
        take_profit_pct=take_profit_pct,
        initial_capital=initial_capital,
    )

    report = (
        f"股票代碼: {stock_code}\n"
        f"初始資金: {initial_capital}\n"
        f"停利百分比: {take_profit_pct}\n"
        f"最終資產: {summary['最終資產']:.2f}\n"
        f"報酬率: {summary['報酬率']:.2f}%"
    )
    await update.message.reply_text(report)
    return ConversationHandler.END
