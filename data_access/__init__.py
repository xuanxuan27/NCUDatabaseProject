# data_access/__init__.py

"""
data_access 目錄的 __init__.py：
這裡把 data_access.py 和 db_config.py 中常用的函式和變數匯出，方便使用 import data_access 直接拿到這些東西。
"""

from .data_access import (
    get_db_connection,
    fetch_stock_data
)
from .db_config import db_cfg

__all__ = [
    "get_db_connection",
    "fetch_stock_data",
    "db_cfg",
]
