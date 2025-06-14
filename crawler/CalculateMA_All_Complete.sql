USE [ncu_database]
GO
/****** Object:  StoredProcedure [dbo].[CalculateMA_All_Complete]    Script Date: 2025/6/2 下午 11:06:40 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[CalculateMA_All_Complete]
AS
BEGIN
    SET NOCOUNT ON;

    -- 利用 Window Function 計算各期移動平均 (MA5, MA10, MA20, MA60, MA120, MA240)
    ;WITH CTE_MA AS (
        SELECT
            [date],
            StockCode,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
              ) AS MA5,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
              ) AS MA10,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
              ) AS MA20,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
              ) AS MA60,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
              ) AS MA120,
            AVG(CAST([Close] AS DECIMAL(10, 2)))
              OVER (
                PARTITION BY StockCode
                ORDER BY [date]
                ROWS BETWEEN 239 PRECEDING AND CURRENT ROW
              ) AS MA240
        FROM stock_price_history_2023_to_2025
    )
    UPDATE st
    SET
        st.MA5   = c.MA5,
        st.MA10  = c.MA10,
        st.MA20  = c.MA20,
        st.MA60  = c.MA60,
        st.MA120 = c.MA120,
        st.MA240 = c.MA240
    FROM stock_price_history_2023_to_2025 AS st
    INNER JOIN CTE_MA AS c
        ON st.StockCode = c.StockCode
       AND st.[date]     = c.[date];
END
