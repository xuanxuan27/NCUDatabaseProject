## 功能特點

### 📥 Data Access

* 直接從 `stock_price_history_2023_to_2025` 取出包含：

  * `Date, Open, High, Low, Close, Volume`
  * `MA5, MA10, MA20, MA60, MA120, MA240`
  * `K_value, D_value`
* 自動把 `Date` 設為 `DatetimeIndex`，方便時間序列分析
* 支援依 `StockCode` 與日期區間 `BETWEEN` 篩選

---

### 📊 Plotting Toolkit

* **K 線＋成交量＋多條移動平均線**

  * 可自訂要畫的 MA（`MA5、MA10、MA20、MA30、MA60、MA120、MA240`）
* **布林帶 (Bollinger Bands)**

  * 可指定中軸 MA（如 `MA20`），亦可 fallback 自行計算 MA
* **相對強弱指數 (RSI)**

  * 以 `Close` 計算 RSI，並標示超買/超賣區域
* **隨機震盪指標 (KD/Stochastic Oscillator)**

  * 直接使用資料表中的 `K_value、D_value`
* **Granville 八條法則圖 (Granville Rules)**

  * Panel0：K 線＋指定 MA（預設 `MA20`）＋R1–R8 各規則標註
  * Panel1：成交量
  * Panel2：價格 vs MA 偏離率
  * Panel3：MA 斜率
  * Panel4：成交量移動平均 (Vol\_MA)
* **黃金交叉 / 死亡交叉圖 (Cross Signals)**

  * 短/長期 MA 交叉標註（預設 `MA5 + MA20`）
* **價格突破 / 跌破圖 (Breakout Signals)**

  * 價格與指定 MA（預設 `MA20`）的突破/跌破標註

---

### 🛠️ 模組化、可擴充

* `data_access.py`、`plot_figure.py`、`db_config.py` 三個獨立模組
* 可自行調整繪圖參數（MA 週期、RSI 週期、KD 週期等）
* 函式皆設有預設值，可直接 Plug-and-Play

---

### 🔧 高度自訂化

* 繪圖函式參數化：

  * 可傳入任意 MA 欄位清單（如 `['MA5','MA10','MA20']`）
  * 可指定布林帶中軸 MA、RSI 週期、KD 讀取欄位
  * 可指定 Granville MA 週期、Vol\_MA 週期、交叉短/長 MA 週期、突破 MA 週期

---

### 📦 易於整合

* 只要放入同一工作資料夾，並在程式開頭 `import plot` 即可使用
* 參考 `example_usage.py` 迅速上手

---

## 環境與安裝

### 要求

* Python 版本：≥ 3.7
* 必要套件：

  * `pandas` ≥ 1.5.0
  * `numpy` ≥ 1.21.0
  * `matplotlib` ≥ 3.5.0
  * `mplfinance` ≥ 0.12.7a0
  * `pyodbc` ≥ 4.0.30

---

### 安裝步驟

1. **建立與啟動虛擬環境（建議）**

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. **安裝依賴套件**

   ```bash
   pip install pandas numpy matplotlib mplfinance pyodbc
   ```

3. **把 `plot` 資料夾放到你的專案根目錄**，保持如下結構：

   ```
   your_project_root/
   ├─ plot/
   │   ├─ __init__.py
   │   ├─ data_access.py
   │   ├─ plot_figure.py
   │   └─ db_config.py
   ├─ example_usage.py
   └─ README.md
   ```

4. **編輯 `plot/db_config.py`**，填入你的資料庫連線參數（參考範例）。

---

## 範例

在 `plot/db_config.py` 中，加入以下內容：

```python
# plot/db_config.py

db_cfg = {
    'driver': 'SQL Server',
    'server': '127.0.0.1',
    'database': '......',
    'uid': '.......',
    'pwd': '......'
}
```

然後在命令列執行以下指令即可看到範例效果：

```bash
python -m plot.example_usage
```
