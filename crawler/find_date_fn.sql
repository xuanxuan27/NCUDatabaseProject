USE [ncu_database]
GO
/****** Object:  UserDefinedFunction [dbo].[find_date_fn]    Script Date: 2025/6/3 下午 11:04:36 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER FUNCTION [dbo].[find_date_fn] (
    @StartDate DATE,
    @Days INT,
    @IncludeToday BIT,
    @Direction NVARCHAR(10)
)
RETURNS TABLE
AS
RETURN (
    WITH FilteredCalendar AS (
        SELECT [date], day_of_stock
        FROM Full_Calendar
        WHERE day_of_stock > 0
    )
    SELECT TOP (@Days + 1) [date], day_of_stock
    FROM FilteredCalendar
    WHERE 
        (@Direction = 'backward' AND [date] <= @StartDate) OR
        (@Direction = 'forward' AND [date] >= @StartDate)
    ORDER BY 
        CASE 
            WHEN @Direction = 'backward' THEN [date] END DESC,
        CASE 
            WHEN @Direction = 'forward' THEN [date] END ASC
);
