## 1. data_access.py
功能：集中處理資料庫連線與資料擷取。

主要函式：

get_db_connection(driver: str, server: str, database: str, uid: str, pwd: str) -> pyodbc.Connection

建立並回傳 PyODBC 連線物件。

fetch_stock_data(conn, stock_code: int, start_date: str, end_date: str) -> pd.DataFrame

以範例 SQL 查詢 StockTrading_TA 表中指定股票代碼、日期範圍的資料。

轉換為 DataFrame 後，以 Date 作為 Index。

若查無資料，回傳空的 DataFrame。

## 2. plot_granville.py
功能：繪製 Granville 八條法則綜合技術圖。

外部相依：

data_access.get_db_connection、data_access.fetch_stock_data

db_config.db_cfg

matplotlib, mplfinance, numpy, pandas

主要流程：

連線並擷取資料 → 檢查是否有資料

計算 Deviation, Slope, Vol_MA5

根據 buy_or_sell 欄位篩選出 R1–R8 訊號，並指定對應顏色與形狀

建立 mpf.make_addplot 清單，包含：

MA20 （Panel 0）

R1–R8 訊號散點圖（Panel 0）

Deviation 折線（Panel 2）

Slope 折線（Panel 3）

Vol_MA5 折線（Panel 4）

呼叫 mpf.plot 繪製五面板圖，並於 Panel0 加 Legend

存檔並關閉圖形

修改紀錄（如需）：

可調整三角形大小（markersize）、顏色、Legend 位置

若欲加入額外面板，可在 panel_ratios 與 addplots 清單增補設定

## 3. plot_all_charts.py
功能：提供多支常見技術指標圖表繪製函式，並在 __main__ 中示範一次生成所有圖表的流程。

外部相依：

data_access.get_db_connection、data_access.fetch_stock_data

db_config.db_cfg

matplotlib, mplfinance, numpy, pandas、matplotlib.dates

模組函式：

plot_candle_and_volume_chart(df, stock_code, save_path) -> str

直接接受 fetch_stock_data 回傳的 DataFrame，繪製 K 線＋成交量＋MA5/MA20/MA60＋Granville Rule 標註。

plot_bollinger(df, window=20, num_std=2, save_path) -> str

計算並繪製布林通道（上下通道 + MA）。

plot_rsi(df, period=14, save_path) -> str

計算並繪製 RSI。

plot_kd(df, k_period=14, d_period=3, save_path) -> str

計算並繪製 KD 隨機指標。

plot_all_charts(stock_code, start_date, end_date, output_prefix, db_config) -> dict

依序呼叫上述四支函式，並回傳產生檔案的路徑字典。