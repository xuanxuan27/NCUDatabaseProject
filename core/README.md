# 核心模組使用指南

## 概述

這是基於 document.md 設計的**必要核心層**實現，提供簡化的葛蘭必八大法則技術分析功能。

## 🎯 架構設計

```
【必要核心層】
├── data_processor.py      ✅ 資料處理模組
├── signal_processor.py    ✅ 訊號產生模組  
├── output_processor.py    ✅ 結果輸出模組
└── main_api.py           ✅ 主要API入口
```

## 🚀 快速開始

### 基本使用

```python
from main_api import analyze_stock
import pandas as pd

# 準備股票資料 (必須包含: date, open, high, low, close, volume)
df = pd.read_csv('your_stock_data.csv')

# 執行分析
response = analyze_stock(
    stock_code="2330",
    historical_data=df
)

# 檢查結果
if response.success:
    print(f"發現 {len(response.data.signals)} 個訊號")
    for signal in response.data.signals:
        print(f"{signal.signal_type} 訊號 (法則 {signal.rule_number})")
```

### 即時資料分析

```python
# 加入即時資料
current_data = {
    'price': 550.5,
    'volume': 25000000,
    'timestamp': datetime.now()
}

response = analyze_stock(
    stock_code="2330", 
    historical_data=df,
    current_data=current_data
)
```

### 自訂配置

```python
from signal_processor import SignalConfig

# 自訂參數
config = SignalConfig(
    ma_period=10,              # 移動平均週期
    volume_period=5,           # 成交量平均週期
    divergence_threshold=2.0,  # 乖離閾值
    enable_signal_filter=True  # 啟用訊號過濾
)

response = analyze_stock("2330", df, config=config)
```

## 📊 API 參考

### 主要函式

#### `analyze_stock()`
完整的股票技術分析

**參數：**
- `stock_code` (str): 股票代碼
- `historical_data` (DataFrame): 歷史OHLCV資料
- `current_data` (dict, 可選): 即時資料
- `config` (SignalConfig, 可選): 分析配置

**回傳：** `APIResponse` 物件

#### `quick_analysis()`
快速分析，適合簡單使用情境

```python
from main_api import quick_analysis

result = quick_analysis("2330", df, ma_period=20)
print(f"訊號數量: {result['signals']}")
```

### 資料結構

#### Signal
```python
@dataclass
class Signal:
    stock_code: str      # 股票代碼
    rule_number: int     # 葛蘭必法則編號 (1-8)
    signal_type: str     # 'BUY' 或 'SELL'
    timestamp: datetime  # 訊號時間
    price: float         # 訊號價格
    confidence: float    # 信心度 (0.0-1.0)
```

#### AnalysisResult
```python
@dataclass
class AnalysisResult:
    stock_code: str                    # 股票代碼
    signals: List[Signal]              # 訊號列表
    latest_indicators: Dict[str, float] # 最新技術指標
    processing_time: float             # 處理時間
    timestamp: datetime                # 分析時間
```

## 🔧 配置選項

### SignalConfig
```python
@dataclass
class SignalConfig:
    ma_period: int = 20                    # 移動平均週期
    volume_period: int = 5                 # 成交量平均週期  
    divergence_threshold: float = 3.0      # 乖離閾值 (%)
    enable_signal_filter: bool = True      # 啟用訊號過濾
```

## 📈 葛蘭必八大法則

### 買進法則 (1-4)
1. **法則1**: 價格跌破均線後首次回升至均線之上
2. **法則2**: 價格在均線之上回檔，接近均線未跌破又再度上升
3. **法則3**: 價格遠離均線後回檔至均線獲支撐後反彈
4. **法則4**: 價格跌破均線且大幅偏離後出現止跌跡象

### 賣出法則 (5-8)
5. **法則5**: 價格突破均線後首次跌破均線
6. **法則6**: 價格在均線之下反彈未突破均線即再度下跌
7. **法則7**: 價格遠離均線後回彈至均線附近遇壓力再下跌
8. **法則8**: 價格突破均線後大幅偏離，然後出現見頂訊號

## 🧪 測試

運行測試套件：
```bash
python test_core_modules.py
```

運行使用範例：
```bash
python example_usage.py
```

## 📋 輸入資料格式

DataFrame 必須包含以下欄位：
```python
required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
```

範例：
```csv
date,open,high,low,close,volume
2024-01-01,550.0,555.0,548.0,552.0,25000000
2024-01-02,552.0,558.0,550.0,555.0,28000000
...
```

## ⚡ 效能指標

### MVP 版本目標
- 單股票分析：< 100ms
- 資料處理：< 50ms
- 訊號產生：< 30ms
- 輸出格式化：< 20ms

## 🔍 故障排除

### 常見問題

**Q: 缺少必要欄位錯誤**
```
DataValidationError: Missing required columns: ['date']
```
**A**: 確保 DataFrame 包含所有必要欄位

**Q: 資料量不足錯誤**
```
SignalProcessingError: Insufficient data: need at least 20 rows
```
**A**: 提供足夠的歷史資料（建議至少30天）

**Q: 沒有產生訊號**
```
signals: []
```
**A**: 這是正常的，表示當前市況不符合任何葛蘭必法則條件

## 🚀 後續擴展

### 可選優化項目
- 🔧 快取管理 (cache_manager.py)
- 🔧 批次處理 (batch_processor.py)  
- 🚀 配置管理 (config_manager.py)
- 🚀 效能監控 (performance_monitor.py)
- 🎯 市場狀態分析 (market_analyzer.py)

### 整合建議
1. 將核心模組集成到您的股票監控服務中
2. 根據實際需求添加可選優化項目
3. 設置定時任務進行批次分析
4. 建立訊號通知機制

## 📞 支援

如有問題或需要協助，請參考：
- `test_core_modules.py` - 完整測試範例
- `example_usage.py` - 使用範例
- `document.md` - 完整架構設計文件 