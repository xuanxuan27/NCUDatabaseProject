# plot/data_access.py

import pyodbc
import pandas as pd

def get_db_connection(driver: str, server: str, database: str, uid: str, pwd: str):
    """
    回傳一個 pyodbc 連線物件，用來跟 SQL Server 建立連線
    """
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};PWD={pwd};"
    )
    return pyodbc.connect(conn_str)

def fetch_stock_data(conn, stock_code: int, start_date: str, end_date: str) -> pd.DataFrame:
    """
    從 stock_price_history_2023_to_2025 取出下面這些欄位：
      Date,
      Open,
      High,
      Low,
      Close,
      Volume,
      MA5,
      MA10,
      MA20,
      MA60,
      MA120,
      MA240,
      K_value,
      D_value

    其中 StockCode、Capacity、Change、Transaction 等因為繪圖無需，所以不撈。
    回傳一張以 Date 做 Index 的 DataFrame。
    """
    sql = """
        SELECT
            [Date],
            [Open],
            [High],
            [Low],
            [Close],
            Volume,
            MA5,
            MA10,
            MA20,
            MA60,
            MA120,
            MA240,
            K_value,
            D_value
        FROM dbo.stock_price_history_2023_to_2025
        WHERE StockCode = ?
          AND [Date] BETWEEN ? AND ?
        ORDER BY [Date]
    """
    df = pd.read_sql(
        sql,
        conn,
        params=[stock_code, start_date, end_date],
        parse_dates=['Date']
    )
    if df.empty:
        return df
    df.set_index('Date', inplace=True)
    return df
