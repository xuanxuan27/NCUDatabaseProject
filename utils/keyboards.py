from telegram import ReplyKeyboardMarkup

# 主選單按鍵
reply_keyboard = [
    ['查詢股價資料', '顯示圖表'],
    ['輸入/移除追蹤標的清單', '追蹤標的清單'],
    ['回測']
]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# 圖表選單按鍵
chart_keyboard = [
    ['K線圖', '布林通道'],
    ['相對強弱指標 (RSI)', 'KD 指標'],
    ['葛蘭碧法則', '交叉訊號'],
    ['突破訊號', '結束']
]
chart_markup = ReplyKeyboardMarkup(chart_keyboard, one_time_keyboard=True, resize_keyboard=True)
