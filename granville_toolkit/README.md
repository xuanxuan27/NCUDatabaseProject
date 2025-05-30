# Granville Eight Rules Technical Indicator Toolkit

一個專為「葛蘭必八大法則」設計的技術指標計算工具包，提供股票技術分析所需的核心指標計算功能。

## 功能特點

- 📈 **移動平均線計算** - 支援 SMA 和 EMA
- 📊 **成交量均線計算** - 分析成交量趨勢
- ⚡ **黃金交叉/死亡交叉訊號** - 自動偵測均線交叉
- 🎯 **突破訊號判斷** - 價格相對均線的突破分析
- 🔥 **葛蘭必八大法則完整實作** - 全部八個法則的精確判斷
- 🛠️ **模組化設計** - 易於擴展和維護

## 安裝與環境設定

### 要求
- Python 3.10.6
- pandas >= 1.5.0
- numpy >= 1.21.0

### 安裝步驟

1. 建立虛擬環境：
```bash
python -m venv venv
```

2. 啟動虛擬環境：
```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

3. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用範例

```python
import pandas as pd
import granville_toolkit as gt

# 準備股票資料（需包含 date, open, high, low, close, volume 欄位）
df = pd.read_csv('stock_data.csv')

# 計算技術指標
df = gt.moving_average(df, window=20, column='close', out_col='ma20')
df = gt.moving_average(df, window=5, column='close', out_col='ma5')
df = gt.volume_average(df, window=5, out_col='vol_ma5')

# 計算交叉訊號
df = gt.crossover_signal(df, short_col='ma5', long_col='ma20', out_col='golden_cross')

# 計算突破訊號
df = gt.breakout_signal(df, price_col='close', ma_col='ma20', out_col='breakout')

# 🎯 完整的葛蘭必八大法則判斷
df = gt.granville_eight_rules(
    df, 
    ma_col='ma20', 
    price_col='close', 
    vol_col='volume',
    vol_ma_col='vol_ma5',
    out_col='granville_signal'
)

# 檢視法則描述
rule_descriptions = gt.get_rule_descriptions()
for rule_num, description in rule_descriptions.items():
    print(f"Rule {rule_num}: {description}")
```

## 葛蘭必八大法則

### 買進法則 (Rules 1-4)

1. **股價跌破均線後首次回升至均線之上（均線走平或轉折向上）**
2. **股價在均線之上回檔，接近均線未跌破又再度上升（均線持續向上）**
3. **股價遠離均線後回檔至均線獲支撐後反彈（均線持續向上）**
4. **股價跌破均線且大幅偏離後出現明顯止跌或反轉，並有量縮跡象（均線由下彎轉平）**

### 賣出法則 (Rules 5-8)

5. **股價突破均線後首次跌破均線（均線走平或轉折向下）**
6. **股價在均線之下反彈未突破均線即再度下跌（均線持續下彎）**
7. **股價遠離均線後回彈至均線附近遇壓力再下跌（均線持續下彎）**
8. **股價突破均線後大幅偏離，然後出現明顯見頂（量縮/價跌），均線由上升轉平甚至下彎**

### 輸入資料格式

DataFrame 必須包含以下欄位：
- `date`: 日期（或作為 index）
- `open`: 開盤價
- `high`: 最高價
- `low`: 最低價
- `close`: 收盤價
- `volume`: 成交量

### 輸出訊號說明

#### 黃金交叉/死亡交叉 (`crossover_signal`)
- `1`: 黃金交叉（短線上穿長線）
- `-1`: 死亡交叉（短線下穿長線）
- `0`: 無交叉訊號

#### 突破訊號 (`breakout_signal`)
- `1`: 價格突破均線上方
- `-1`: 價格跌破均線下方
- `0`: 無突破訊號

#### 葛蘭必八大法則 (`granville_eight_rules`)
- `1-4`: 買進法則編號
- `5-8`: 賣出法則編號
- `0`: 無符合法則條件

## API 文件

### 基礎指標函式

#### `moving_average(df, window=20, column="close", ma_type="sma", out_col="ma20")`
計算移動平均線

**參數：**
- `window`: 計算期數
- `column`: 來源欄位名稱
- `ma_type`: "sma" 或 "ema"
- `out_col`: 輸出欄位名稱

#### `volume_average(df, window=5, out_col="vol_ma5")`
計算成交量均線

#### `crossover_signal(df, short_col="ma5", long_col="ma20", out_col="golden_cross")`
偵測均線交叉訊號

#### `breakout_signal(df, price_col="close", ma_col="ma20", out_col="breakout")`
偵測價格突破訊號

### 葛蘭必法則函式

#### `granville_eight_rules(df, ma_col="ma20", price_col="close", vol_col="volume", **kwargs)`
完整的葛蘭必八大法則判斷

**參數：**
- `ma_col`: 移動平均線欄位名稱
- `price_col`: 價格欄位名稱
- `vol_col`: 成交量欄位名稱
- `vol_ma_col`: 成交量均線欄位名稱
- `divergence_threshold`: 價格偏離閾值（預設3.0%）
- `trend_window`: 趨勢計算視窗（預設5）
- `support_tolerance`: 支撐/壓力容忍度（預設0.5%）
- `out_col`: 輸出欄位名稱

#### `get_rule_descriptions()`
取得所有法則的中文描述

## 測試

執行基礎測試：
```bash
python test_toolkit.py
```

## 專案結構

```
granville_toolkit/
├── __init__.py           # 套件初始化與匯出
├── indicators.py         # 基礎技術指標計算
├── granville_rules.py    # 葛蘭必八大法則實作
├── utils.py             # 輔助函式（趨勢判斷、資料驗證等）
├── exceptions.py        # 自訂例外類別
requirements.txt         # 依賴套件清單
test_toolkit.py         # 測試腳本
README.md               # 專案說明文件
GB_document.md          # 技術規格文件
```

## 功能特色

### 📊 精確的法則判斷
- 完整實作所有八個葛蘭必法則
- 考慮均線趨勢、價格偏離、成交量變化
- 支撐/壓力位測試機制

### 🔧 高度可配置
- 所有參數皆可自訂調整
- 支援不同時間週期的均線
- 靈活的閾值設定

### 🛡️ 強健的錯誤處理
- 完整的資料驗證機制
- 清晰的錯誤訊息
- 自訂例外類別

### 📈 效能最佳化
- 向量化計算
- 記憶體效率考量
- 大量資料處理能力

## 版本歷史

- **v0.1.0** - 初始版本，包含完整的葛蘭必八大法則實作

## 注意事項

- 輸入資料需依日期升冪排序
- 建議至少30個交易日的資料以獲得穩定的訊號
- 所有函式都會保留原始資料並新增指標欄位
- 法則觸發具有互斥性，每個時點只會觸發一個法則

## 後續開發規劃

- [ ] 增加回測框架
- [ ] 提供視覺化功能
- [ ] 增加更多技術指標
- [ ] 效能進一步最佳化
- [ ] 支援即時資料串流 