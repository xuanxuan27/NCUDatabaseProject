import pyodbc

db_cfg = {
    'driver': 'driver',
    'server': 'server',
    'database': 'database name',
    'uid': 'user name',
    'pwd': 'password'
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