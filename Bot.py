import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler
)
from handlers.menu import start, handle_menu_selection
from handlers.query_stock import query_stock
from handlers.detail_chart import handle_chart_type, handle_stock_code_chart, handle_date_range_and_generate_chart

# 日誌設定
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 狀態碼區分模組
WAITING_FOR_STOCK_CODE = 1  # 查詢股價用
WAITING_FOR_CHART_TYPE = 101  # 顯示圖表：第一步選圖類型
WAITING_FOR_STOCK_CODE_CHART = 102  # 顯示圖表：輸入股票代碼
WAITING_FOR_DATE_RANGE = 103

if __name__ == '__main__':
    bot_token = "your token"

    try:
        app = ApplicationBuilder().token(bot_token).build()

        # 查詢股價流程 Handler
        conv_handler_query = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^查詢股價資料$'), handle_menu_selection)
            ],
            states={
                WAITING_FOR_STOCK_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, query_stock)
                ]
            },
            fallbacks=[CommandHandler("start", start)]
        )

        #圖表查詢流程 Handler
        conv_handler_chart = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^顯示圖表$'), handle_menu_selection)
            ],
            states={
                WAITING_FOR_CHART_TYPE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_type)
                ],
                WAITING_FOR_STOCK_CODE_CHART: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_code_chart)
                ],
                WAITING_FOR_DATE_RANGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_range_and_generate_chart)
                ]
            },
            fallbacks=[CommandHandler("start", start)]
        )

        # 啟用所有對話流程
        app.add_handler(CommandHandler("start", start))
        app.add_handler(conv_handler_query)
        app.add_handler(conv_handler_chart)

        logging.info("Bot 開始運作...")
        app.run_polling()

    except Exception as e:
        logging.critical(f"Bot 初始化或運作失敗: {e}")
