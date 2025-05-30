"""
Implementation of Granville's Eight Rules for trading signals
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .utils import (
    validate_dataframe, 
    calculate_ma_trend, 
    is_price_diverged,
    detect_new_highs_lows,
    detect_volume_contraction,
    detect_price_crossover,
    detect_support_resistance_test
)


def granville_eight_rules(
    df: pd.DataFrame, 
    ma_col: str = "ma20", 
    price_col: str = "close", 
    vol_col: str = "volume",
    vol_ma_col: str = "vol_ma5",
    divergence_threshold: float = 3.0,
    trend_window: int = 5,
    support_tolerance: float = 0.5,
    out_col: str = "granville_signal"
) -> pd.DataFrame:
    """
    Apply Granville's Eight Rules for comprehensive trading signals
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with price, MA, and volume data
    ma_col : str, default="ma20"
        Moving average column name
    price_col : str, default="close"
        Price column name
    vol_col : str, default="volume"
        Volume column name
    vol_ma_col : str, default="vol_ma5" 
        Volume moving average column name
    divergence_threshold : float, default=3.0
        Percentage threshold for price divergence from MA
    trend_window : int, default=5
        Window for MA trend calculation
    support_tolerance : float, default=0.5
        Tolerance percentage for support/resistance detection
    out_col : str, default="granville_signal"
        Output signal column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with Granville rule signals (1-8) or 0 for no signal
    """
    required_cols = [ma_col, price_col, vol_col]
    if vol_ma_col in df.columns:
        required_cols.append(vol_ma_col)
    
    validate_dataframe(df, required_cols)
    
    result_df = df.copy()
    
    # Extract series for calculations
    price = df[price_col]
    ma = df[ma_col]
    volume = df[vol_col]
    
    # If volume MA not provided, calculate it
    if vol_ma_col not in df.columns:
        vol_ma = volume.rolling(window=5).mean()
    else:
        vol_ma = df[vol_ma_col]
    
    # Calculate supporting indicators
    ma_trend = calculate_ma_trend(ma, window=trend_window)
    far_above_ma, far_below_ma = is_price_diverged(price, ma, divergence_threshold)
    new_highs, new_lows = detect_new_highs_lows(price, window=10)
    volume_contraction = detect_volume_contraction(volume, vol_ma)
    cross_above, cross_below = detect_price_crossover(price, ma)
    support_test, resistance_test = detect_support_resistance_test(price, ma, support_tolerance)
    
    # Initialize signal column
    signals = pd.Series(0, index=df.index)
    
    # Apply each rule
    signals = _apply_rule_1(signals, cross_above, ma_trend)
    signals = _apply_rule_2(signals, price, ma, new_highs, ma_trend)
    signals = _apply_rule_3(signals, price, ma, far_above_ma, support_test, ma_trend)
    signals = _apply_rule_4(signals, price, ma, far_below_ma, volume_contraction, ma_trend, new_lows)
    signals = _apply_rule_5(signals, cross_below, ma_trend)
    signals = _apply_rule_6(signals, price, ma, new_lows, ma_trend)
    signals = _apply_rule_7(signals, price, ma, far_below_ma, resistance_test, ma_trend)
    signals = _apply_rule_8(signals, price, ma, far_above_ma, volume_contraction, ma_trend, new_highs)
    
    result_df[out_col] = signals
    
    return result_df


def _apply_rule_1(signals: pd.Series, cross_above: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 1: Price crosses above MA when MA is flat or turning up (Buy)
    """
    ma_flat_or_up = ma_trend >= 0
    rule_1_condition = cross_above & ma_flat_or_up
    
    signals.loc[rule_1_condition & (signals == 0)] = 1
    return signals


def _apply_rule_2(signals: pd.Series, price: pd.Series, ma: pd.Series, 
                  new_highs: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 2: Price above MA, pullback without breaking MA, then new high (Buy)
    """
    price_above_ma = price > ma
    ma_uptrend = ma_trend > 0
    
    # Look for new highs while staying above MA during uptrend
    rule_2_condition = price_above_ma & new_highs & ma_uptrend
    
    signals.loc[rule_2_condition & (signals == 0)] = 2
    return signals


def _apply_rule_3(signals: pd.Series, price: pd.Series, ma: pd.Series,
                  far_above_ma: pd.Series, support_test: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 3: Price far above MA, pullback to MA support, then bounce (Buy)
    """
    ma_uptrend = ma_trend > 0
    
    # Price was far above MA, now testing support at MA level
    rule_3_condition = (
        far_above_ma.shift(3).fillna(False) |  # Was far above MA recently
        far_above_ma.shift(2).fillna(False) |
        far_above_ma.shift(1).fillna(False)
    ) & support_test & ma_uptrend
    
    signals.loc[rule_3_condition & (signals == 0)] = 3
    return signals


def _apply_rule_4(signals: pd.Series, price: pd.Series, ma: pd.Series,
                  far_below_ma: pd.Series, volume_contraction: pd.Series, 
                  ma_trend: pd.Series, new_lows: pd.Series) -> pd.Series:
    """
    Rule 4: Price far below MA, volume contraction, no new lows, MA turning flat (Buy)
    """
    ma_flat_or_turning_up = ma_trend >= -0.5  # MA no longer strongly declining
    no_new_lows = ~new_lows
    
    # Price oversold with volume drying up and no new lows
    rule_4_condition = (
        far_below_ma & 
        volume_contraction & 
        no_new_lows &
        ma_flat_or_turning_up
    )
    
    signals.loc[rule_4_condition & (signals == 0)] = 4
    return signals


def _apply_rule_5(signals: pd.Series, cross_below: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 5: Price crosses below MA when MA is flat or turning down (Sell)
    """
    ma_flat_or_down = ma_trend <= 0
    rule_5_condition = cross_below & ma_flat_or_down
    
    signals.loc[rule_5_condition & (signals == 0)] = 5
    return signals


def _apply_rule_6(signals: pd.Series, price: pd.Series, ma: pd.Series,
                  new_lows: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 6: Price below MA, bounce fails to break MA, then new low (Sell)
    """
    price_below_ma = price < ma
    ma_downtrend = ma_trend < 0
    
    # Look for new lows while staying below MA during downtrend
    rule_6_condition = price_below_ma & new_lows & ma_downtrend
    
    signals.loc[rule_6_condition & (signals == 0)] = 6
    return signals


def _apply_rule_7(signals: pd.Series, price: pd.Series, ma: pd.Series,
                  far_below_ma: pd.Series, resistance_test: pd.Series, ma_trend: pd.Series) -> pd.Series:
    """
    Rule 7: Price far below MA, bounce to MA resistance, then decline (Sell)
    """
    ma_downtrend = ma_trend < 0
    
    # Price was far below MA, now testing resistance at MA level
    rule_7_condition = (
        far_below_ma.shift(3).fillna(False) |  # Was far below MA recently
        far_below_ma.shift(2).fillna(False) |
        far_below_ma.shift(1).fillna(False)
    ) & resistance_test & ma_downtrend
    
    signals.loc[rule_7_condition & (signals == 0)] = 7
    return signals


def _apply_rule_8(signals: pd.Series, price: pd.Series, ma: pd.Series,
                  far_above_ma: pd.Series, volume_contraction: pd.Series,
                  ma_trend: pd.Series, new_highs: pd.Series) -> pd.Series:
    """
    Rule 8: Price far above MA, volume contraction, no new highs, MA turning flat (Sell)
    """
    ma_flat_or_turning_down = ma_trend <= 0.5  # MA no longer strongly rising
    no_new_highs = ~new_highs
    
    # Price overbought with volume drying up and no new highs
    rule_8_condition = (
        far_above_ma & 
        volume_contraction & 
        no_new_highs &
        ma_flat_or_turning_down
    )
    
    signals.loc[rule_8_condition & (signals == 0)] = 8
    return signals


def get_rule_descriptions() -> Dict[int, str]:
    """
    Get descriptions for each Granville rule
    
    Returns:
    --------
    Dict[int, str]
        Dictionary mapping rule numbers to descriptions
    """
    return {
        1: "價格跌破均線後首次回升至均線之上（均線走平或轉折向上）- 買進",
        2: "價格在均線之上回檔，接近均線未跌破又再度上升（均線持續向上）- 買進", 
        3: "價格遠離均線後回檔至均線獲支撐後反彈（均線持續向上）- 買進",
        4: "價格跌破均線且大幅偏離後出現明顯止跌或反轉，並有量縮跡象（均線由下彎轉平）- 買進",
        5: "價格突破均線後首次跌破均線（均線走平或轉折向下）- 賣出",
        6: "價格在均線之下反彈未突破均線即再度下跌（均線持續下彎）- 賣出",
        7: "價格遠離均線後回彈至均線附近遇壓力再下跌（均線持續下彎）- 賣出",
        8: "價格突破均線後大幅偏離，然後出現明顯見頂（量縮/價跌），均線由上升轉平甚至下彎 - 賣出"
    } 