import warnings
import pandas as pd
import numpy as np
import granville_toolkit as gt
from data_access.data_access import get_db_connection, fetch_stock_data
from data_access.db_config import db_cfg
import math

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def prepare_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算 MA5、MA20、vol_ma5，並產生:
      - granville_signal
      - cross_signal (黃金/死亡交叉)
      - breakout_signal (突破/跌破 MA20)
    """
    df = df.copy()
    if 'MA5' not in df.columns:
        df['MA5'] = df['Close'].rolling(5).mean()
    if 'MA20' not in df.columns:
        df['MA20'] = df['Close'].rolling(20).mean()
    if 'vol_ma5' not in df.columns:
        df['vol_ma5'] = df['Volume'].rolling(5).mean()

    # Granville 八大法則
    df['ma20_lower'] = df['MA20']
    df['vol_ma5_lower'] = df['vol_ma5']
    df = gt.granville_eight_rules(
        df,
        ma_col='ma20_lower',
        price_col='Close',
        vol_col='Volume',
        vol_ma_col='vol_ma5_lower',
        out_col='granville_signal'
    )

    # 黃金/死亡交叉
    df = gt.crossover_signal(
        df,
        short_col='MA5',
        long_col='MA20',
        out_col='cross_signal'
    )

    # 突破/跌破 MA20
    df = gt.breakout_signal(
        df,
        price_col='Close',
        ma_col='MA20',
        out_col='breakout_signal'
    )

    return df

def backtest_single_stock_enhanced(
    df: pd.DataFrame,
    stock_id: str,
    take_profit_pct: float = 0.1,
    initial_capital: float = 1_000_000
):
    """
    進行回測後，回傳一個 summary dict，其中包含：
      1. '交易歷史': pd.DataFrame（每筆交易明細）
      2. '策略總結表':  pd.DataFrame（ID, stock_id, total_return, win_rate, total_trades, sharpe_ratio）

    交易邏輯：
      - 空倉時：如果 granville_signal ∈ {1,2,3,4} 且 (cross_signal==1 或 breakout_signal==1)，於當日收盤買入
      - 持倉時：如果當日最高價 ≥ 停利價 (Close*(1+take_profit_pct))，或 granville_signal ∈ {5,6,7,8}，或 cross_signal == -1，或 breakout_signal == -1，於當日收盤前賣出
      - 回測結束時，若仍持有，則以最後一日收盤價賣出
    """
    # 取得「葛蘭必八大法則」的中文敘述字典
    rule_descriptions = gt.get_rule_descriptions()

    df = df.sort_index().copy()
    cash = initial_capital
    shares = 0
    entry_price = 0.0
    last_close = df.iloc[-1]['Close']

    transaction_records = []

    for idx, row in df.iterrows():
        date = idx
        close = row['Close']
        high = row['High']
        gran = int(row['granville_signal'])
        cross = int(row['cross_signal'])
        brk = int(row['breakout_signal'])
        tp_price = entry_price * (1 + take_profit_pct)

        # 持倉 > 0 時，檢查是否要賣出
        if shares > 0:
            rule_used = ""
            # 1) 停利條件
            if high >= entry_price * (1 + take_profit_pct):
                sell_price = entry_price * (1 + take_profit_pct)
                rule_used = "停利 - 賣出"
            # 2) 葛蘭必賣訊
            elif gran in [5,6,7,8]:
                sell_price = close
                rule_used = rule_descriptions.get(gran, "")
            # 3) 死亡交叉
            elif cross == -1:
                sell_price = close
                rule_used = "死亡交叉 - 賣出"
            # 4) 跌破均線
            elif brk == -1:
                sell_price = close
                rule_used = "跌破均線 - 賣出"
            else:
                sell_price = None

            if sell_price is not None:
                txn_amount = sell_price * shares
                profit = (sell_price - entry_price) * shares
                cash += txn_amount
                total_capital = cash
                transaction_records.append({
                    '交易日期': date.strftime('%Y-%m-%d'),
                    '交易類型': '賣出',
                    '股票代碼': stock_id,
                    '成交價格': round(sell_price, 2),
                    '股數': float(shares),
                    '交易金額': round(txn_amount, 2),
                    '剩餘資金': round(cash, 2),
                    '獲利金額': round(profit, 2),
                    '總資金': round(total_capital, 2),
                    '交易規則': rule_used
                })
                shares = 0

        # 空倉時，檢查是否要買入
        if shares == 0:
            if gran in [1,2,3,4] and (cross == 1 or brk == 1):
                buy_price = close
                shares = math.floor(cash / buy_price)
                if shares > 0:
                    txn_amount = buy_price * shares
                    cash -= txn_amount
                    total_capital = cash + shares * close
                    rule_used = rule_descriptions.get(gran, "")
                    entry_price = buy_price
                    transaction_records.append({
                        '交易日期': date.strftime('%Y-%m-%d'),
                        '交易類型': '買入',
                        '股票代碼': stock_id,
                        '成交價格': round(buy_price, 2),
                        '股數': float(shares),
                        '交易金額': round(txn_amount, 2),
                        '剩餘資金': round(cash, 2),
                        '獲利金額': 0.0,
                        '總資金': round(total_capital, 2),
                        '交易規則': rule_used
                    })

    # 回測最後一天若仍持有，則以最後收盤價賣出
    if shares > 0:
        sell_price = last_close
        txn_amount = sell_price * shares
        profit = (sell_price - entry_price) * shares
        cash += txn_amount
        total_capital = cash
        last_gran = int(df.iloc[-1]['granville_signal'])
        if last_gran in [5,6,7,8]:
            rule_used = rule_descriptions.get(last_gran, "")
        else:
            rule_used = "收盤強制 - 賣出"
        transaction_records.append({
            '交易日期': df.index[-1].strftime('%Y-%m-%d'),
            '交易類型': '賣出',
            '股票代碼': stock_id,
            '成交價格': round(sell_price, 2),
            '股數': float(shares),
            '交易金額': round(txn_amount, 2),
            '剩餘資金': round(cash, 2),
            '獲利金額': round(profit, 2),
            '總資金': round(total_capital, 2),
            '交易規則': rule_used
        })
        shares = 0

    final_value = cash

    # 建立「交易歷史」DataFrame
    trades_df = pd.DataFrame(transaction_records)
    if trades_df.empty:
        trades_df = pd.DataFrame(columns=[
            '交易日期','交易類型','股票代碼','成交價格','股數',
            '交易金額','剩餘資金','獲利金額','總資金','交易規則'
        ])

    # 計算績效指標
    total_return = (final_value - initial_capital) / initial_capital

    sell_df = trades_df[trades_df['交易類型'] == '賣出'].copy()
    total_trades = len(sell_df)
    wins = sell_df[sell_df['獲利金額'] > 0].shape[0]
    win_rate = wins / total_trades if total_trades > 0 else 0.0

    # 計算 Sharpe ratio
    # 每筆賣出 return_ratio = 獲利金額 / (entry_price*股數)
    # 由於無 entry_price*股數，只能用：
    # return_ratio = 獲利金額 / (交易金額 - 獲利金額)
    sell_df['return_ratio'] = (
        sell_df['獲利金額'] /
        (sell_df['交易金額'] - sell_df['獲利金額'])
    )
    rets = sell_df['return_ratio'].dropna()
    if len(rets) > 1 and rets.std() != 0:
        sharpe = rets.mean() / rets.std() * np.sqrt(len(rets))
    else:
        sharpe = 0.0

    # ===== 組合「策略總結表」 =====
    summary_table = pd.DataFrame([{
        'stock_id': stock_id,
        'total_return': total_return,   # 小數，若要百分比可 *100
        'win_rate': win_rate,
        'total_trades': total_trades,
        'sharpe_ratio': sharpe
    }])
    # 加上自動遞增 id 欄（IDENTITY(1,1)）
    summary_table.insert(0, 'id', range(1, len(summary_table)+1))

    # 最後把所有要回傳的都打包成一個 dict
    summary = {
        '起始資金': initial_capital,
        '最終資產': final_value,
        '報酬率': total_return * 100,
        '最終持倉': {
            '股票代號': stock_id,
            '持有股數': shares,
            '最新收盤': last_close,
            '持倉市值': shares * last_close
        },
        '交易歷史': trades_df,
        '策略總結表': summary_table
    }

    return summary

