import logging
from utils.config import BOT_TOKEN
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler
)
from handlers.menu import start, handle_menu_selection
from handlers.query_stock import query_stock
from handlers.detail_chart import handle_chart_type, handle_stock_code_chart, handle_date_range_and_generate_chart
from handlers.watch_list import handle_watchlist_input
from handlers.backtest_h import receive_stock_code, receive_take_profit, receive_initial_capital

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 狀態碼
START = 0
WAITING_FOR_STOCK_CODE = 1
WAITING_FOR_WATCHLIST_INPUT = 20
WAITING_FOR_CHART_TYPE = 101
WAITING_FOR_STOCK_CODE_CHART = 102
WAITING_FOR_DATE_RANGE = 103
WAITING_FOR_STOCK_CODE_b = 301
WAITING_FOR_TAKE_PROFIT = 302
WAITING_FOR_INITIAL_CAPITAL = 303


if __name__ == '__main__':
    bot_token = BOT_TOKEN

    try:
        app = ApplicationBuilder().token(bot_token).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection)],
                WAITING_FOR_STOCK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, query_stock)],
                WAITING_FOR_WATCHLIST_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_watchlist_input)],
                WAITING_FOR_CHART_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_type)],
                WAITING_FOR_STOCK_CODE_CHART: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_code_chart)],
                WAITING_FOR_DATE_RANGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_range_and_generate_chart)],
                WAITING_FOR_STOCK_CODE_b: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_stock_code)],
                WAITING_FOR_TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_take_profit)],
                WAITING_FOR_INITIAL_CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_initial_capital)],
            },
            fallbacks=[CommandHandler("start", start)],
            allow_reentry=True
        )

        app.add_handler(conv_handler)

        logging.info("Bot 開始運作...")
        app.run_polling()

    except Exception as e:
        logging.critical(f"Bot 初始化或運作失敗: {e}")
