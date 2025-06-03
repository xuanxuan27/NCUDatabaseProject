@echo off
chcp 65001 >nul
cd /d "D:\碩一\資料庫系統實作專題\Final_project"

REM 啟動虛擬環境 (若存在)
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

REM 執行 Python 爬蟲程式
python "D:\碩一\資料庫系統實作專題\Final_project\StockData_Calculate_ma_kd.py"


pause

