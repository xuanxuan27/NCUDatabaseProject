import pyodbc

db_cfg = {
    'driver': 'SQL Server',
    'server': '127.0.0.1',
    'database': 'stock_database',
    'uid': '110502025',
    'pwd': '1234'
}

def get_db_connection(cfg):
    conn_str = (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['uid']};"
        f"PWD={cfg['pwd']};"
    )
    return pyodbc.connect(conn_str)