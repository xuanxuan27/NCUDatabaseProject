USE [ncu_database]
GO
/****** Object:  StoredProcedure [dbo].[Calculate_KD_Values]    Script Date: 2025/6/2 下午 11:06:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- 使用 cursor 計算 KD 並更新表格
ALTER PROCEDURE [dbo].[Calculate_KD_Values]
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @K_value FLOAT, @D_value FLOAT;
    DECLARE @RSV REAL;
    DECLARE @today_c FLOAT;
    DECLARE @row_number INT;  --用來查看是否換到另一家公司
    DECLARE @StockCode VARCHAR(100);
    DECLARE @Date DATE;
    DECLARE @yesterday_K FLOAT, @yesterday_D FLOAT;

    SET @yesterday_K = 50;  --設定第一筆資料 昨日 K 值為50
    SET @yesterday_D = 50;  --設定第一筆資料 昨日 D 值為50

    -- 開啟cursor，將 trading_stock 根據StockCode 進行分組，
    -- 並依照 Date 生序排列，再給予每組各自的 row number
    DECLARE cur CURSOR FOR
    SELECT ROW_NUMBER() OVER (PARTITION BY StockCode ORDER BY Date ASC) AS ROW_ID,
           StockCode, [Date], [Close]
    FROM stock_price_history_2023_to_2025;

    OPEN cur;
    FETCH NEXT FROM cur INTO @row_number, @StockCode, @Date, @today_c;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- 若是每間公司的第一筆，初始化 KD 為 50
        IF (@row_number = 1)  -- 若Row_number = 1 ，表示換到下一間公司，重新設定初始KD值
        BEGIN
            SET @yesterday_K = 50;
            SET @yesterday_D = 50;
        END

        -- 計算 RSV（以 9 天為週期）
		/*
        SELECT @RSV = 
            CASE WHEN (MAX(High) - MIN(Low)) = 0 THEN 0
                 ELSE (@today_c - MIN(Low)) * 100.0 / (MAX(High) - MIN(Low))
            END
		*/
		SELECT @RSV = (@today_c - MIN(Low)) * 100.0 / (MAX(High) - MIN(Low))
        FROM stock_price_history_2023_to_2025
        WHERE StockCode = @StockCode
          AND [Date] IN (
              SELECT [Date] FROM find_date_fn(@Date, 9, 1, 'backward')
          );
        --GROUP BY StockCode;

        -- 計算 K 值與 D 值
        SET @K_value = (2.0 / 3.0) * @yesterday_K + (1.0 / 3.0) * @RSV;
        SET @D_value = (2.0 / 3.0) * @yesterday_D + (1.0 / 3.0) * @K_value;

		PRINT '---';
		PRINT 'StockCode: ' + @StockCode;
		PRINT 'Date: ' + CAST(@Date AS VARCHAR);
		PRINT 'Close: ' + CAST(@today_c AS VARCHAR);
		PRINT 'RSV: ' + CAST(@RSV AS VARCHAR);
		PRINT 'K: ' + CAST(@K_value AS VARCHAR);
		PRINT 'D: ' + CAST(@D_value AS VARCHAR);


        -- 更新當日 K 與 D 值
        UPDATE stock_price_history_2023_to_2025
        SET K_value = @K_value,
            D_value = @D_value
        WHERE StockCode = @StockCode AND [Date] = @Date;

        -- 今日的 KD 作為明日的昨日值
        SET @yesterday_K = @K_value;
        SET @yesterday_D = @D_value;

        FETCH NEXT FROM cur INTO @row_number, @StockCode, @Date, @today_c;
    END

    CLOSE cur;
    DEALLOCATE cur;

END;

/*
執行 procedure
EXEC dbo.Calculate_KD_Values

查表
SELECT * FROM StockTrading_TA ORDER BY StockCode ASC, Date ASC;
*/