**轉換為Markdown格式**

他們要求提供兩份READMEs並使用Markdown格式。已經提供了純文字內容，包括標題。我的任務是將這些內容轉換為Markdown格式，包含適當的標頭（#、##），程式區塊，以及清單。如果文本已

已思考 7 秒鐘

# data\_access README

`data_access` 模組負責與資料庫連線並擷取股票歷史資料，提供簡單易用的介面供上層模組（如回測、繪圖）使用。

---

## 模組結構

```plaintext
data_access/
├── __init__.py
├── data_access.py
└── db_config.py
```

* **`data_access.py`**

  * `get_db_connection(...)`：建立並回傳一個 `pyodbc.Connection` 物件。
  * `fetch_stock_data(conn, stock_code, start_date, end_date)`：使用已建立的連線擷取指定股票代碼與日期區間的歷史資料，回傳 `pandas.DataFrame`。

* **`db_config.py`**

  * `db_cfg`：一個字典，用來儲存資料庫連線參數（driver、server、database、uid、pwd）。
  * 使用時可直接匯入 `db_cfg` 作為 `get_db_connection` 的參數。

---

## 安裝與設定

1. **安裝必要套件**

   ```bash
   pip install pyodbc pandas
   ```

   * `pyodbc >= 4.0.30`：與 SQL Server 建立 ODBC 連線
   * `pandas >= 1.5.0`：資料整理與操作

2. **設定資料庫連線參數**
   在 `data_access/db_config.py` 中填入你的資料庫資訊，範例如下：

   ```python
   # data_access/db_config.py

   db_cfg = {
       'driver': 'SQL Server',      # ODBC Driver 名稱
       'server': '127.0.0.1',        # SQL Server 主機 IP 或名稱
       'database': 'your_database',  # 資料庫名稱
       'uid': 'your_username',       # 帳號
       'pwd': 'your_password'        # 密碼
   }
   ```

   請根據實際環境修改 `driver`、`server`、`database`、`uid`、`pwd`，並將檔案儲存。

---

## 功能說明

### `get_db_connection(driver: str, server: str, database: str, uid: str, pwd: str) -> pyodbc.Connection`

* **功能**
  建立並回傳一個 `pyodbc.Connection` 連線物件，用於後續執行 SQL 查詢。

* **參數**

  * `driver` (`str`)：ODBC Driver 名稱（例如 `"SQL Server"` 或 `"ODBC Driver 17 for SQL Server"`）。
  * `server` (`str`)：資料庫伺服器位址（IP、主機名稱或 Domain）。
  * `database` (`str`)：資料庫名稱。
  * `uid` (`str`)：使用者帳號。
  * `pwd` (`str`)：使用者密碼。

* **回傳值**

  * 成功回傳一個 `pyodbc.Connection` 物件。
  * 若連線失敗，會拋出 `pyodbc.Error` 或其他例外，可於呼叫處自行捕捉並處理。

* **範例**

  ```python
  from data_access.data_access import get_db_connection
  from data_access.db_config import db_cfg

  # 使用 db_config.py 中的參數
  conn = get_db_connection(
      driver   = db_cfg['driver'],
      server   = db_cfg['server'],
      database = db_cfg['database'],
      uid      = db_cfg['uid'],
      pwd      = db_cfg['pwd']
  )
  ```

---

### `fetch_stock_data(conn, stock_code: int, start_date: str, end_date: str) -> pd.DataFrame`

* **功能**
  從資料庫的 `stock_price_history_2023_to_2025`（或對應的歷史資料表）讀取指定股票代碼與日期區間的 OHLCV 資料及技術指標欄位。

* **參數**

  * `conn`：透過 `get_db_connection` 建立的 `pyodbc.Connection` 物件。
  * `stock_code` (`int`)：欲查詢的股票代碼，例如 `2330`、`2317`。
  * `start_date` (`str`)：開始日期（格式：`YYYY-MM-DD`）。
  * `end_date` (`str`)：結束日期（格式：`YYYY-MM-DD`）。

* **資料表欄位**
  查詢 SQL 會選取以下欄位（請確保你的資料庫中表格對應欄位存在）：

  ```plaintext
  Date,       -- 日期
  Open,       -- 開盤價
  High,       -- 最高價
  Low,        -- 最低價
  Close,      -- 收盤價
  Volume,     -- 成交量
  MA5,        -- 5 日均線
  MA10,       -- 10 日均線
  MA20,       -- 20 日均線
  MA60,       -- 60 日均線
  MA120,      -- 120 日均線
  MA240,      -- 240 日均線
  K_value,    -- 隨機指標 K 值
  D_value     -- 隨機指標 D 值
  ```

  * 請將下面 SQL 查詢中的 `stock_price_history_2023_to_2025` 換成你資料庫中正確的表名稱。

* **回傳值**

  * 若有資料，回傳 `pd.DataFrame`，並將 `Date` 欄位設為 `DatetimeIndex`。
  * 若無資料（DataFrame 為空），直接回傳空的 `DataFrame`。

* **範例**

  ```python
  import pandas as pd
  from data_access.data_access import get_db_connection, fetch_stock_data
  from data_access.db_config import db_cfg

  # 1. 建立連線
  conn = get_db_connection(**db_cfg)

  # 2. 擷取股票歷史資料 (以 2317 為例)
  df = fetch_stock_data(conn, stock_code=2317, start_date='2023-01-01', end_date='2023-06-30')

  # 3. 關閉連線
  conn.close()

  # 4. 檢視 DataFrame
  if df.empty:
      print("查無資料")
  else:
      print(df.head())
      #          Open   High    Low  Close   Volume   MA5    MA10   MA20   MA60      MA120   MA240  K_value    D_value
      # Date
      # 2023-01-02  152.0  155.0  150.0  154.0  1200000  153.4  152.1  151.2  148.7  145.3    140.0  68.34    47.80
      # ...
  ```

---

## 使用建議與注意事項

1. **連線效率**

   * `get_db_connection` 建立 ODBC 連線的開銷較高，若在短時間內多次呼叫，建議重複使用同一個 `conn`，避免頻繁開/關連線。
   * 查詢資料量大時，建議加上分批查詢或調整 SQL 條件。

2. **資料排序**

   * `fetch_stock_data` 自動對結果使用 `ORDER BY Date` 排序，因此回傳的 `DataFrame` 為「日期由前到後（升冪）」。
   * 若需要不同排序，可自行在取回後以 `df.sort_index(ascending=False)` 等方式調整。

3. **時間格式**

   * `start_date`, `end_date` 必須為 `YYYY-MM-DD` 格式字串。
   * 若資料庫存的是 datetime 時間戳，這組查詢仍會把 `Date` 轉成 `datetime64[ns]` 並設為 index。

4. **欄位名稱對應**

   * 若你資料庫的歷史資料表欄位名稱不完全相同（例如 `STOCKCODE`、`交易量`…），請修改 `data_access.py` 裡的 SQL 查詢對應。
   * 預設 SQL 範例：

     ```sql
     SELECT
       [Date], [Open], [High], [Low], [Close], [Volume],
       MA5, MA10, MA20, MA60, MA120, MA240,
       K_value, D_value
     FROM dbo.stock_price_history_2023_to_2025
     WHERE StockCode = ?
       AND Date BETWEEN ? AND ?
     ORDER BY Date;
     ```


