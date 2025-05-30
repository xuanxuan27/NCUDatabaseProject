"""
Utility functions for Granville Toolkit
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple


def validate_dataframe(df: pd.DataFrame, required_cols: list) -> None:
    """
    Validate input DataFrame has required columns
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to validate
    required_cols : list
        List of required column names
        
    Raises:
    -------
    ValueError
        If required columns are missing
    """
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Required columns {missing_cols} not found in DataFrame")


def calculate_ma_trend(ma_series: pd.Series, window: int = 5) -> pd.Series:
    """
    Calculate moving average trend direction
    
    Parameters:
    -----------
    ma_series : pd.Series
        Moving average values
    window : int, default=5
        Window for trend calculation
        
    Returns:
    --------
    pd.Series
        Trend direction: 1 (up), -1 (down), 0 (flat)
    """
    # Calculate slope over window
    ma_slope = ma_series.diff(window)
    
    # Define trend based on slope
    trend = pd.Series(0, index=ma_series.index)
    trend[ma_slope > 0.001] = 1   # Upward trend
    trend[ma_slope < -0.001] = -1  # Downward trend
    
    return trend


def is_price_diverged(price: pd.Series, ma: pd.Series, threshold_pct: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """
    Check if price significantly diverges from moving average
    
    Parameters:
    -----------
    price : pd.Series
        Price series
    ma : pd.Series  
        Moving average series
    threshold_pct : float, default=3.0
        Divergence threshold percentage
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (far_above_ma, far_below_ma) boolean series
    """
    price_deviation_pct = ((price - ma) / ma) * 100
    
    far_above_ma = price_deviation_pct > threshold_pct
    far_below_ma = price_deviation_pct < -threshold_pct
    
    return far_above_ma, far_below_ma


def detect_new_highs_lows(price: pd.Series, window: int = 10) -> Tuple[pd.Series, pd.Series]:
    """
    Detect new highs and lows within rolling window
    
    Parameters:
    -----------
    price : pd.Series
        Price series
    window : int, default=10
        Window for high/low detection
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (new_highs, new_lows) boolean series
    """
    rolling_max = price.rolling(window=window).max()
    rolling_min = price.rolling(window=window).min()
    
    new_highs = (price == rolling_max) & (price == price.rolling(window=2).max())
    new_lows = (price == rolling_min) & (price == price.rolling(window=2).min())
    
    return new_highs, new_lows


def detect_volume_contraction(volume: pd.Series, vol_ma: pd.Series, threshold: float = 0.8) -> pd.Series:
    """
    Detect volume contraction (volume shrinking)
    
    Parameters:
    -----------
    volume : pd.Series
        Volume series
    vol_ma : pd.Series
        Volume moving average
    threshold : float, default=0.8
        Contraction threshold (volume/vol_ma ratio)
        
    Returns:
    --------
    pd.Series
        Boolean series indicating volume contraction
    """
    volume_ratio = volume / vol_ma
    return volume_ratio < threshold


def detect_price_crossover(price: pd.Series, ma: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Detect price crossover above/below moving average
    
    Parameters:
    -----------
    price : pd.Series
        Price series
    ma : pd.Series
        Moving average series
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (cross_above, cross_below) boolean series
    """
    price_above_ma_today = price > ma
    price_below_ma_yesterday = price.shift(1) <= ma.shift(1)
    cross_above = price_above_ma_today & price_below_ma_yesterday
    
    price_below_ma_today = price < ma
    price_above_ma_yesterday = price.shift(1) >= ma.shift(1)
    cross_below = price_below_ma_today & price_above_ma_yesterday
    
    return cross_above, cross_below


def detect_support_resistance_test(price: pd.Series, ma: pd.Series, tolerance: float = 0.5) -> Tuple[pd.Series, pd.Series]:
    """
    Detect when price tests support/resistance at MA level
    
    Parameters:
    -----------
    price : pd.Series
        Price series
    ma : pd.Series
        Moving average series
    tolerance : float, default=0.5
        Tolerance percentage for support/resistance test
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (support_test, resistance_test) boolean series
    """
    price_pct_diff = ((price - ma) / ma) * 100
    
    # Support test: price approaches MA from below
    support_test = (price_pct_diff.abs() <= tolerance) & (price <= ma)
    
    # Resistance test: price approaches MA from above  
    resistance_test = (price_pct_diff.abs() <= tolerance) & (price >= ma)
    
    return support_test, resistance_test 