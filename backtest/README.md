---

# backtest README

`backtest` 模組提供基於「MA5 / MA20 + Granville 八大法則 + 黃金/死亡交叉 + 突破/跌破」的單一股票回測功能，並支援停利及持倉結束後的資金分配計算。支援直接輸出交易歷史與策略績效彙總表。

---

## 模組結構

```plaintext
backtest/
├── __init__.py
└── backtest.py
```

* **`backtest.py`**

  * `prepare_signals(df: pd.DataFrame) -> pd.DataFrame`：

    1. 計算並新增 `MA5`、`MA20`、`vol_ma5` 欄位（若原始資料中不存在）。
    2. 呼叫 `granville_toolkit.granville_eight_rules`，產生 `granville_signal`。
    3. 呼叫 `granville_toolkit.crossover_signal`，產生 `cross_signal`（黃金/死亡交叉）。
    4. 呼叫 `granville_toolkit.breakout_signal`，產生 `breakout_signal`（突破/跌破 MA20）。
    5. 回傳含上述所有欄位、且 `Date` 已是 `DatetimeIndex` 的 `DataFrame`。

  * `backtest_single_stock_enhanced(df: pd.DataFrame, stock_id: str, config_id: int = 1, take_profit_pct: float = 0.1, initial_capital: float = 1_000_000) -> dict`：
    根據以下規則對單一股票執行回測，回傳包含「交易歷史」與「策略總結表」的字典：

    **交易規則：**

    1. **空倉進場**：

       * 條件：`granville_signal ∈ {1,2,3,4}` 且 `(cross_signal == 1 或 breakout_signal == 1)`
       * 動作：當日收盤價格買入（滿足條件才買），買進股數＝`floor(cash / 收盤價)`
       * 記錄交易：`交易日期`、`交易類型=買入`、`成交價格`、`股數`、`交易金額`、`剩餘資金`、`獲利金額=0`、`總資金`、`交易規則=Granville法則中文`

    2. **持倉賣出**：

       * 條件 A：當日最高價 ≥ 停利價 (`Close * (1 + take_profit_pct)`) → 以停利價賣出，`交易規則=停利賣出`
       * 條件 B：`granville_signal ∈ {5,6,7,8}` → 以當日收盤價賣出，`交易規則=Granville法則中文`
       * 條件 C：`cross_signal == -1`（死亡交叉）→ 以當日收盤價賣出，`交易規則=死亡交叉賣出`
       * 條件 D：`breakout_signal == -1`（跌破均線）→ 以當日收盤價賣出，`交易規則=跌破均線賣出`
       * 賣出之後：計算 `交易金額 = 賣出價 × 股數`，`獲利金額 = (賣出價 - entry_price) × 股數`，更新 `cash`，並記錄：`交易日期`、`交易類型=賣出`、`成交價格`、`股數`、`交易金額`、`剩餘資金`、`獲利金額`、`總資金`、`交易規則`

    3. **最後強制平倉**：

       * 若回測結束時仍持有股票（`shares > 0`），則以最後一日 `Close` 價賣出；
       * 如果最後一日 `granville_signal ∈ {5,6,7,8}`，`交易規則` 取對應法則中文；否則標為 `"收盤強制賣出"`。

    4. **計算績效指標**：

       * **交易歷史**：回測過程中所有「買入」及「賣出」每筆交易都會儲存在一個 `pandas.DataFrame`（欄位：`交易日期, 交易類型, 股票代碼, 成交價格, 股數, 交易金額, 剩餘資金, 獲利金額, 總資金, 交易規則`）。

       * **策略總結表**：回測結束後，統計「賣出」筆數計算：

         * `total_return`（累積報酬率，浮點，`(最終資產 - 起始資金) / 起始資金`）
         * `win_rate`（勝率＝`賣出筆數中獲利筆數 / 賣出筆數`）
         * `total_trades`（賣出次數）
         * `sharpe_ratio`（以各筆賣出回報率計算，`mean / std * sqrt(n)`）

       * 此策略總結表會被放入一個 `pandas.DataFrame`，並加入 `id` 欄（IDENTITY 模擬）。

    * **回傳值**：一個 Python `dict`，結構如下：

      ```python
      {
        '起始資金': float,
        '最終資產': float,
        '報酬率': float,   # 百分比
        '最終持倉': {
          '股票代號': str,
          '持有股數': float,
          '最新收盤': float,
          '持倉市值': float
        },
        '交易歷史': pd.DataFrame,   # 每筆買入 / 賣出詳情
        '策略總結表': pd.DataFrame  # 欄位：id, config_id, stock_id, total_return, win_rate, total_trades, sharpe_ratio
      }
      ```

---

## 安裝與設定

1. **安裝必要套件**

   ```bash
   pip install pandas numpy granville_toolkit
   ```

   * `pandas >= 1.5.0`、`numpy >= 1.21.0`：處理資料與數值計算
   * `granville_toolkit`：計算 Granville 八大法則、交叉、突破等技術指標

2. **確保 `data_access` 可用**
   請先依照 [data\_access README](#data_access-readme) 進行資料庫連線設定，並確保 `data_access` 可以正常匯入，才能讓回測順利取得股價資料。

---

## 使用範例

1. 執行範例：

   ```bash
   python -m tests.test_backtest
   ```

2. 輸出範例結果（僅示意）：

   ```plaintext
   === 回測結果摘要 ===
   起始資金：1000000.00
   最終資產：1314652.00
   報酬率：31.47%

   === 最終持倉狀況 ===
   股票代號：2317
   持有股數：0.0
   最新收盤：1050.00
   持倉市值：0.00

   === 交易歷史 ===
     交易日期 交易類型 股票代碼  成交價格   股數    交易金額   剩餘資金  獲利金額    總資金     交易規則
   2023-03-29   買入   2317   103.50  9552.0  988632.00    98.53    0.00  988730.53   正乖離過大
   2023-04-07   賣出   2317   103.00  9552.0  983856.00  983954.53  -4776.00  983954.53  負乖離過大
   2023-04-14   買入   2317   104.50  9415.0  983867.50    87.03    0.00  983954.53   正乖離過大
   2023-04-24   賣出   2317   103.50  9415.0  974452.50  974539.53  -9415.00  974539.53  負乖離過大
   2023-05-02   買入   2317   106.00  9193.0  974458.00    81.53    0.00  974539.53  一般訊號
   2023-05-12   賣出   2317   102.50  9193.0  942282.50  942364.03 -32175.50  942364.03  死亡交叉賣出

   === 策略總結表 ===
    id  config_id stock_id  total_return  win_rate  total_trades  sharpe_ratio
     1          1     2317       0.0500     0.50             2        0.7071
   ```

---

## API 參考

### `prepare_signals(df: pd.DataFrame) -> pd.DataFrame`

* **參數**

  * `df` (`pd.DataFrame`)：原始歷史股價 `DataFrame`，必須包含以下欄位並以 `Date` 為 index：

    ```plaintext
    ['Open', 'High', 'Low', 'Close', 'Volume', 'MA5', 'MA20', 'vol_ma5'（可在此函式中自動生成）]
    ```

* **功能**

  1. 如果 `df` 不包含 `MA5`、`MA20`、`vol_ma5` 欄位，將自動加上（分別計算 5 日、20 日均線與 5 日成交量均線）。
  2. 計算 `granville_signal`（呼叫 `granville_eight_rules`）。
  3. 計算 `cross_signal`（呼叫 `crossover_signal`）。
  4. 計算 `breakout_signal`（呼叫 `breakout_signal`）。

* **回傳值**

  * 加工後的 `pd.DataFrame`，包含以下欄位：

    ```plaintext
    ['Open', 'High', 'Low', 'Close', 'Volume',
     'MA5', 'MA20', 'vol_ma5',
     'granville_signal', 'cross_signal', 'breakout_signal']
    ```
  * `Date` 已是 `DatetimeIndex`。

---

### `backtest_single_stock_enhanced(df: pd.DataFrame, stock_id: str, config_id: int = 1, take_profit_pct: float = 0.1, initial_capital: float = 1_000_000) -> dict`

* **參數**

  * `df` (`pd.DataFrame`)：必須是經過 `prepare_signals(df)` 處理後的 `DataFrame`，包含 `granville_signal`、`cross_signal`、`breakout_signal`。
  * `stock_id` (`str`)：欲回測之股票代碼（如 `"2317"`）。
  * `config_id` (`int`)：策略參數編號，可任意指定，會放到「策略總結表」中的 `config_id` 欄位。
  * `take_profit_pct` (`float`)：停利百分比（預設 0.1 → 10%）。
  * `initial_capital` (`float`)：回測的初始資金（預設 1,000,000）。

* **功能**

  1. 依照指定策略與信號，自動模擬「買入 → 賣出」過程，包含停利與訊號退場。
  2. 交易期間「現金」與「持股」狀態即時更新，每筆「買入」與「賣出」都會記錄成一筆交易紀錄。
  3. 回測結束後若有剩餘持股策略會自動強制以最後收盤價賣出。
  4. 計算全程交易的「累積報酬率」、「勝率」、「總交易次數」、「夏普比率」。
  5. 整理出：

     * `交易歷史`（`pd.DataFrame`）
     * `策略總結表`（`pd.DataFrame`，帶 `id` 自增）

* **回傳值** (`dict`)

  ```python
  {
    '起始資金': float,             # 回測時所使用的 initial_capital
    '最終資產': float,             # 回測結束後手中現金（+若留股，則加上最後價值）
    '報酬率': float,               # 百分比，如 31.47
    '最終持倉': {
       '股票代號': str,
       '持有股數': float,
       '最新收盤': float,
       '持倉市值': float
    },
    '交易歷史': pd.DataFrame,       # 每筆買入/賣出之詳細紀錄
    '策略總結表': pd.DataFrame      # 只含一筆：id, config_id, stock_id, total_return, win_rate, total_trades, sharpe_ratio
  }
  ```

* **`交易歷史` DataFrame 欄位**

  ```plaintext
  [
    '交易日期',   # YYYY-MM-DD
    '交易類型',   # '買入' / '賣出'
    '股票代碼',   # stock_id
    '成交價格',   # 當日收盤或停利價
    '股數',       # 買進或賣出的股數
    '交易金額',   # 成交價格 × 股數
    '剩餘資金',   # 交易後手上現金
    '獲利金額',   # (賣出價 - entry_price) × 股數；買入時填 0
    '總資金',     # 如果持股為 0，就等於「剩餘資金」；持股時則是 cash + holdings * close
    '交易規則'    # 中文說明：Granville 法則、停利、死亡交叉、跌破均線等
  ]
  ```

* **`策略總結表` DataFrame 欄位**

  ```plaintext
  [
    'id',           # 自動遞增 (IDENTITY 模擬)
    'stock_id',     # 傳入的股票代碼
    'total_return', # 累積報酬率 (小數格式，如 0.3147)
    'win_rate',     # 勝率 (float)
    'total_trades', # 總交易次數 (int)
    'sharpe_ratio'  # 夏普比率 (float)
  ]
  ```

---

## 進階指南與注意事項

1. **Granville 法則中文**

   * 透過 `granville_toolkit.get_rule_descriptions()` 取得一個 `dict[int→中文描述]`，範例：

     ```python
     {
       1: "突破且上揚均線－買進",
       2: "回測均線獲得支撐－買進",
       3: "跌破均線後支持再彈－買進",
       4: "負乖離過大－買進",
       5: "正乖離過大－賣出",
       6: "跌破下降均線－賣出",
       7: "反彈無力無法突破均線－賣出",
       8: "超買回檔賣出(反轉)－賣出"
     }
     ```
   * 若 `granville_signal` 在 1–4 時代表「買進」法則；5–8 代表「賣出」法則。

2. **停利價格**

   * `tp_price = close * (1 + take_profit_pct)`，只有當天的 `High >= tp_price` 時，才會「以停利價」賣出。

3. **最後強制賣出**

   * 如果最後一天 `granville_signal ∈ {5,6,7,8}`，就延續當天的 Granville 賣出法則；否則強制標為 `"收盤強制賣出"`。

4. **Sharpe Ratio 計算**

   * 以每筆「賣出」的回報率 (`return_ratio = 獲利金額/(entry_price×股數)`) 為基礎。
   * 由於程式中難以直接取得 `entry_price×股數`，用近似方式：

     ```python
     return_ratio = 獲利金額 / (交易金額 - 獲利金額)
     ```
   * 最後計算 `Sharpe = mean(rets) / std(rets) * sqrt(n)`，若樣本數 ≤ 1 或標準差為 0，則預設 `sharpe = 0.0`。

5. **多次回測 & 參數優化**

   * 若要同時回測多組 `config_id`、不同 `take_profit_pct`、不同 `initial_capital`，可在外部迴圈中針對每組參數呼叫 `backtest_single_stock_enhanced`，收集並合併多張「策略總結表」以做比較。
   * 例如：

     ```python
     results = []
     for pid, tp in enumerate([0.05, 0.1, 0.15], start=1):
         sum_dict = backtest_single_stock_enhanced(df, "2317", config_id=pid, take_profit_pct=tp, initial_capital=1_000_000)
         results.append(sum_dict['策略總結表'])
     all_summary = pd.concat(results, ignore_index=True)
     print(all_summary.to_string(index=False))
     ```
---

## 專案範例

```plaintext
NCUDatabaseProject/
│
├─ backtest/
│   ├─ __init__.py
│   └─ backtest.py
│
└─ README.md
```

* **執行回測範例**

  ```bash
  python -m tests.test_backtest
  ```

  會依序印出：

  1. 回測結果摘要
  2. 最終持倉狀況
  3. 交易歷史（DataFrame 表格）
  4. 策略總結表（DataFrame）

* **若想在自訂腳本中使用**

  ```python
  from data_access.data_access import get_db_connection, fetch_stock_data
  from data_access.db_config import db_cfg
  from backtest.backtest import prepare_signals, backtest_single_stock_enhanced

  # 讀資料、執行回測、處理結果
  ```
