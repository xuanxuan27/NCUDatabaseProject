"""
Technical indicators for Granville Eight Rules analysis
"""

import pandas as pd
import numpy as np
from typing import Union, Literal
from .utils import validate_dataframe


def moving_average(
    df: pd.DataFrame, 
    window: int = 20, 
    column: str = "close", 
    ma_type: Literal["sma", "ema"] = "sma", 
    out_col: str = "ma20"
) -> pd.DataFrame:
    """
    Calculate moving average for specified column
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with OHLCV data
    window : int, default=20
        Period for moving average calculation
    column : str, default="close"
        Source column for calculation
    ma_type : {"sma", "ema"}, default="sma"
        Type of moving average - Simple MA or Exponential MA
    out_col : str, default="ma20"
        Output column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with added moving average column
    
    Raises:
    -------
    ValueError
        If required column is missing from input DataFrame
    """
    validate_dataframe(df, [column])
    
    result_df = df.copy()
    
    if ma_type == "sma":
        result_df[out_col] = df[column].rolling(window=window).mean()
    elif ma_type == "ema":
        result_df[out_col] = df[column].ewm(span=window, adjust=False).mean()
    else:
        raise ValueError("ma_type must be either 'sma' or 'ema'")
    
    return result_df


def volume_average(
    df: pd.DataFrame, 
    window: int = 5, 
    out_col: str = "vol_ma5"
) -> pd.DataFrame:
    """
    Calculate volume moving average
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with volume data
    window : int, default=5
        Period for volume average calculation
    out_col : str, default="vol_ma5"
        Output column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with added volume average column
    
    Raises:
    -------
    ValueError
        If volume column is missing from input DataFrame
    """
    validate_dataframe(df, ["volume"])
    
    result_df = df.copy()
    result_df[out_col] = df["volume"].rolling(window=window).mean()
    
    return result_df


def crossover_signal(
    df: pd.DataFrame, 
    short_col: str = "ma5", 
    long_col: str = "ma20", 
    out_col: str = "golden_cross"
) -> pd.DataFrame:
    """
    Detect golden cross and death cross signals
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with moving average columns
    short_col : str, default="ma5"
        Short-term moving average column name
    long_col : str, default="ma20" 
        Long-term moving average column name
    out_col : str, default="golden_cross"
        Output signal column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with crossover signals:
        1: Golden cross (short MA crosses above long MA)
        -1: Death cross (short MA crosses below long MA)
        0: No crossover
    
    Raises:
    -------
    ValueError
        If required columns are missing from input DataFrame
    """
    validate_dataframe(df, [short_col, long_col])
    
    result_df = df.copy()
    
    # Calculate crossover signals
    short_ma = df[short_col]
    long_ma = df[long_col]
    
    # Current and previous day comparison
    short_above_long_today = short_ma > long_ma
    short_above_long_yesterday = short_ma.shift(1) <= long_ma.shift(1)
    
    short_below_long_today = short_ma < long_ma
    short_below_long_yesterday = short_ma.shift(1) >= long_ma.shift(1)
    
    # Golden cross: short MA crosses above long MA
    golden_cross = short_above_long_today & short_above_long_yesterday
    
    # Death cross: short MA crosses below long MA  
    death_cross = short_below_long_today & short_below_long_yesterday
    
    # Assign signals
    result_df[out_col] = 0
    result_df.loc[golden_cross, out_col] = 1
    result_df.loc[death_cross, out_col] = -1
    
    return result_df


def breakout_signal(
    df: pd.DataFrame, 
    price_col: str = "close", 
    ma_col: str = "ma20", 
    out_col: str = "breakout"
) -> pd.DataFrame:
    """
    Detect price breakout signals relative to moving average
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with price and moving average data
    price_col : str, default="close"
        Price column for breakout analysis
    ma_col : str, default="ma20"
        Moving average reference column
    out_col : str, default="breakout"
        Output signal column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with breakout signals:
        1: Price breaks above MA
        -1: Price breaks below MA
        0: No breakout
    
    Raises:
    -------
    ValueError
        If required columns are missing from input DataFrame
    """
    validate_dataframe(df, [price_col, ma_col])
    
    result_df = df.copy()
    
    price = df[price_col]
    ma = df[ma_col]
    
    # Today's price vs MA and yesterday's comparison
    price_above_ma_today = price > ma
    price_below_ma_yesterday = price.shift(1) <= ma.shift(1)
    
    price_below_ma_today = price < ma
    price_above_ma_yesterday = price.shift(1) >= ma.shift(1)
    
    # Breakout above: price crosses above MA
    breakout_above = price_above_ma_today & price_below_ma_yesterday
    
    # Breakout below: price crosses below MA
    breakout_below = price_below_ma_today & price_above_ma_yesterday
    
    # Assign signals
    result_df[out_col] = 0
    result_df.loc[breakout_above, out_col] = 1
    result_df.loc[breakout_below, out_col] = -1
    
    return result_df


def granville_rules(
    df: pd.DataFrame, 
    ma_col: str = "ma20", 
    price_col: str = "close", 
    vol_col: str = "volume", 
    out_col: str = "granville_signal"
) -> pd.DataFrame:
    """
    Apply Granville's Eight Rules for trading signals
    
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
    out_col : str, default="granville_signal"
        Output signal column name
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with Granville rule signals (1-8) or 0 for no signal
    
    Note:
    -----
    This function requires the specific logic for each of the 8 Granville rules
    to be implemented. Currently returns placeholder logic.
    """
    required_cols = [ma_col, price_col, vol_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Required columns {missing_cols} not found in DataFrame")
    
    result_df = df.copy()
    
    # TODO: Implement specific Granville Eight Rules logic
    # This is a placeholder implementation
    # The actual implementation requires detailed specification of each rule
    
    result_df[out_col] = 0
    
    # Placeholder warning
    import warnings
    warnings.warn(
        "granville_rules function contains placeholder logic. "
        "Please provide specific Granville Eight Rules criteria for full implementation.",
        UserWarning
    )
    
    return result_df


def calculate_rsi(df, period=14, out_col='RSI'):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df[out_col] = 100 - (100 / (1 + rs))
    return df


def calculate_kd(df, n=9, m1=3, m2=3, out_k='K', out_d='D'):
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df[out_k] = rsv.ewm(com=m1-1, adjust=False).mean()
    df[out_d] = df[out_k].ewm(com=m2-1, adjust=False).mean()
    return df 