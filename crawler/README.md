* 資料表：
    * `stock_price_history_2023_to_2025`
    * `stock_price_realtime_2025`
* `.sql`檔：
    * `CalculateMA_All_Complete.sql` (stored procedure)
    * `Calculate_KD_Values.sql` (stored procedure)
        * `find_date_fn.sql` (user define function) 上述計算KD用中用到的


`.py`檔都更改 MSSQL 連線參數後：
* `StockData_history_practice.py`
   直接執行可將歷史資料 ([Date]
      ,[StockCode]
      ,[Capacity]
      ,[Volume]
      ,[Open]
      ,[High]
      ,[Low]
      ,[Close]
      ,[Change]
      ,[Transaction]) 都input進 ssms中的 `stock_price_history_2023_to_2025`資料表

* `StockData_realtime.py`、
`run_stock_data_collector_for_final_project.bat `
   在工作排程器中建立此工作，設定在 ==每天 上午8:57== 觸發，`.bat`中需更改為本地路徑。
   此程式會在 mon-fri ：
    *    ==8:58== 清空 `stock_price_realtime_2025` 表
    *    ==09:00–13:30== 每分鐘執行一次爬蟲
    *    ==14:00== 把10支股票當日的收盤資料更新到`stock_price_history_2023_to_2025`(所以每日會增加10筆上去)
    *    更新的資料欄位同上
    
* `StockData_Calculate_ma_kd.py`、
`run_stock_data_calculate_for_final_project.bat`  
   在工作排程器中建立此工作，設定在 ==每天 下午2:04== 觸發，`.bat`中需更改為本地路徑。
   (用到上述 `.sql`檔)

   此程式會在 mon-fri ：
    *    ==14:05== `check_and_run_sp()`
        * 先從 `stock_price_history_2023_to_2025` 取出當天 ([Date] = 今天) 篩選 10 支股票的筆數，如果筆數 ≥ 10，表示當天 10 支股票的日線資料都已插入。
        * 若筆數足夠，就呼叫 `call_stored_procedures()`，否則在日誌記錄「歷史資料不齊全，跳過 MA/KD 計算」
