import aiohttp
import json
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.menu import markup

async def query_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock_code = update.message.text.strip()
    if stock_code == '0':
        await update.message.reply_text("結束查詢", reply_markup=markup)
        return ConversationHandler.END

    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw&json=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            text = await response.text()

            if response.status != 200:
                await update.message.reply_text("⚠️ 無法取得資料，請稍後再試。")
                return ConversationHandler.END

            data = json.loads(text)
            try:
                stock_data = data['msgArray'][0]
                name = stock_data['n']
                code = stock_data['c']
                price = stock_data['z']
                high = stock_data['h']
                low = stock_data['l']
                open_price = stock_data['o']
                volume = stock_data['v']
                prev_close = stock_data["y"]

                reply = (
                    f"📈 {name} ({code})\n"
                    f"昨日收盤價：{prev_close}\n"
                    f"開盤價：{open_price}\n"
                    f"最高價：{high}\n"
                    f"最低價：{low}\n"
                    f"成交價：{price}\n"
                    f"成交量：{volume}"
                )
            except Exception as e:
                reply = "⚠️ 找不到該股票代碼，請重新輸入。"

            await update.message.reply_text(reply)
            return 1