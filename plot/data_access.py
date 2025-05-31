import pyodbc
import pandas as pd

def get_db_connection(driver: str, server: str, database: str, uid: str, pwd: str):
    """
    Returns a pyodbc connection object.
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
    Fetches stock data between dates and returns a DataFrame indexed by Date.
    """
    sql = (
        "SELECT [Date], [Open], [High], [Low], [Close], Volume, MA5, MA20, MA60, buy_or_sell "
        "FROM dbo.StockTrading_TA "
        "WHERE StockCode = ? "
        "  AND Date BETWEEN ? AND ? "
        "ORDER BY Date"
    )
    df = pd.read_sql(sql, conn, params=[stock_code, start_date, end_date], parse_dates=['Date'])
    if df.empty:
        return df
    df.set_index('Date', inplace=True)
    return df