"""
Signal Processing Module

This module handles:
- Technical indicator calculations using granville_toolkit
- Granville Eight Rules signal generation
- Basic signal filtering and validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

# Import from existing granville_toolkit
from granville_toolkit import (
    moving_average,
    volume_average,
    granville_eight_rules,
    get_rule_descriptions
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Signal data structure as defined in document.md"""
    stock_code: str
    rule_number: int  # 1-8 for Granville rules
    signal_type: str  # 'BUY' or 'SELL'
    timestamp: datetime
    price: float
    confidence: float  # 0.0-1.0


@dataclass
class SignalConfig:
    """Signal configuration as defined in document.md"""
    ma_period: int = 20
    volume_period: int = 5
    divergence_threshold: float = 3.0
    enable_signal_filter: bool = True


class SignalProcessingError(Exception):
    """Custom exception for signal processing errors"""
    pass


def generate_signals(
    df: pd.DataFrame, 
    config: Optional[SignalConfig] = None
) -> List[Signal]:
    """
    Generate Granville signals from processed DataFrame
    
    Args:
        df: Processed OHLCV DataFrame
        config: Signal configuration parameters
        
    Returns:
        List of Signal objects
    """
    if config is None:
        config = SignalConfig()
    
    try:
        logger.info(f"Generating signals with MA period: {config.ma_period}")
        
        # Step 1: Calculate technical indicators
        indicators_df = calculate_indicators(
            df, 
            ma_window=config.ma_period,
            vol_window=config.volume_period
        )
        
        # Step 2: Apply Granville rules
        raw_signals = _apply_granville_rules(indicators_df, config)
        
        # Step 3: Filter signals if enabled
        if config.enable_signal_filter:
            filtered_signals = filter_signals(raw_signals, time_window_minutes=5)
        else:
            filtered_signals = raw_signals
        
        logger.info(f"Generated {len(filtered_signals)} filtered signals from {len(raw_signals)} raw signals")
        return filtered_signals
        
    except Exception as e:
        logger.error(f"Error generating signals: {str(e)}")
        raise SignalProcessingError(f"Signal generation failed: {str(e)}")


def calculate_indicators(
    df: pd.DataFrame, 
    ma_window: int = 20,
    vol_window: int = 5
) -> pd.DataFrame:
    """
    Calculate technical indicators required for Granville rules
    
    Args:
        df: Input OHLCV DataFrame
        ma_window: Moving average window
        vol_window: Volume average window
        
    Returns:
        DataFrame with added technical indicators
    """
    if df.empty:
        raise SignalProcessingError("Input DataFrame is empty")
    
    if len(df) < max(ma_window, vol_window):
        raise SignalProcessingError(f"Insufficient data: need at least {max(ma_window, vol_window)} rows")
    
    indicators_df = df.copy()
    
    try:
        # Calculate moving averages using granville_toolkit
        indicators_df = moving_average(
            df=indicators_df, 
            window=ma_window, 
            column='close',
            out_col='ma'
        )
        
        indicators_df = volume_average(
            df=indicators_df, 
            window=vol_window,
            out_col='vol_avg'
        )
        
        # Additional indicators for Granville rules
        indicators_df['ma_slope'] = _calculate_ma_slope(indicators_df['ma'])
        indicators_df['price_ma_ratio'] = indicators_df['close'] / indicators_df['ma']
        indicators_df['volume_ratio'] = indicators_df['volume'] / indicators_df['vol_avg']
        
        # Price change and momentum
        indicators_df['price_change'] = indicators_df['close'].pct_change()
        indicators_df['price_change_3d'] = indicators_df['close'].pct_change(periods=3)
        
        logger.info("Technical indicators calculated successfully")
        return indicators_df
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        raise SignalProcessingError(f"Indicator calculation failed: {str(e)}")


def filter_signals(
    signals: List[Signal], 
    time_window_minutes: int = 5
) -> List[Signal]:
    """
    Filter signals to prevent duplicates and noise
    
    Args:
        signals: List of raw signals
        time_window_minutes: Time window for duplicate detection
        
    Returns:
        Filtered list of signals
    """
    if not signals:
        return signals
    
    # Sort signals by timestamp
    sorted_signals = sorted(signals, key=lambda x: x.timestamp)
    filtered_signals = []
    
    for signal in sorted_signals:
        # Check for recent similar signals
        is_duplicate = False
        
        for existing_signal in filtered_signals:
            time_diff = abs((signal.timestamp - existing_signal.timestamp).total_seconds() / 60)
            
            # Consider duplicate if same stock, same rule, within time window
            if (signal.stock_code == existing_signal.stock_code and 
                signal.rule_number == existing_signal.rule_number and
                time_diff < time_window_minutes):
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_signals.append(signal)
    
    logger.info(f"Signal filtering: {len(sorted_signals)} -> {len(filtered_signals)}")
    return filtered_signals


def _apply_granville_rules(df: pd.DataFrame, config: SignalConfig) -> List[Signal]:
    """
    Apply Granville Eight Rules to generate signals
    
    Args:
        df: DataFrame with technical indicators
        config: Signal configuration
        
    Returns:
        List of raw signals
    """
    signals = []
    stock_code = "UNKNOWN"  # Will be set by caller
    
    try:
        # Prepare data for granville_eight_rules function
        analysis_df = df.copy()
        
        # Add required columns if not present
        if 'ma20' not in analysis_df.columns:
            analysis_df['ma20'] = analysis_df['ma']
        if 'vol_ma5' not in analysis_df.columns:
            analysis_df['vol_ma5'] = analysis_df['vol_avg']
        
        # Use existing granville_toolkit function
        result_df = granville_eight_rules(
            df=analysis_df,
            ma_col='ma20',
            price_col='close',
            vol_col='volume',
            vol_ma_col='vol_ma5',
            divergence_threshold=config.divergence_threshold
        )
        
        # Extract signals from the result DataFrame
        if 'granville_signal' in result_df.columns:
            signal_series = result_df['granville_signal']
            
            # Find the latest non-zero signal
            latest_signals = signal_series[signal_series != 0]
            
            if not latest_signals.empty:
                # Get the most recent signal
                latest_signal_idx = latest_signals.index[-1]
                rule_num = int(latest_signals.iloc[-1])
                
                # Determine signal type (1-4 are BUY, 5-8 are SELL)
                signal_type = "BUY" if rule_num <= 4 else "SELL"
                
                # Calculate confidence based on various factors
                confidence = _calculate_signal_confidence(df, rule_num, latest_signal_idx)
                
                # Get current price and timestamp
                current_price = float(df['close'].iloc[latest_signal_idx])
                if 'date' in df.columns:
                    current_timestamp = df['date'].iloc[latest_signal_idx]
                else:
                    current_timestamp = datetime.now()
                
                signal = Signal(
                    stock_code=stock_code,
                    rule_number=rule_num,
                    signal_type=signal_type,
                    timestamp=current_timestamp,
                    price=current_price,
                    confidence=confidence
                )
                
                signals.append(signal)
                logger.info(f"Generated {signal_type} signal for rule {rule_num} with confidence {confidence:.2f}")
        
        return signals
        
    except Exception as e:
        logger.error(f"Error applying Granville rules: {str(e)}")
        # Instead of raising error, return empty list to allow processing to continue
        logger.warning("Returning empty signals list due to error")
        return []


def _calculate_ma_slope(ma_series: pd.Series, periods: int = 3) -> pd.Series:
    """
    Calculate moving average slope to determine trend direction
    
    Args:
        ma_series: Moving average series
        periods: Number of periods for slope calculation
        
    Returns:
        Series with MA slope values
    """
    return ma_series.diff(periods) / periods


def _calculate_signal_confidence(df: pd.DataFrame, rule_number: int, position: int) -> float:
    """
    Calculate signal confidence based on market conditions and technical factors
    
    Args:
        df: DataFrame with indicators
        rule_number: Granville rule number (1-8)
        position: Position in the data where signal occurred
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    base_confidence = 0.6  # Base confidence level
    
    try:
        # Factor 1: Volume confirmation
        vol_factor = 0.0
        if 'volume_ratio' in df.columns and position < len(df):
            vol_ratio = df['volume_ratio'].iloc[position]
            if vol_ratio > 1.5:  # High volume
                vol_factor = 0.2
            elif vol_ratio > 1.2:  # Moderate volume
                vol_factor = 0.1
        
        # Factor 2: Trend strength
        trend_factor = 0.0
        if 'ma_slope' in df.columns and position < len(df):
            ma_slope = abs(df['ma_slope'].iloc[position])
            if not pd.isna(ma_slope):
                trend_factor = min(0.2, ma_slope * 10)  # Scale slope to max 0.2
        
        # Factor 3: Price momentum
        momentum_factor = 0.0
        if 'price_change_3d' in df.columns and position < len(df):
            momentum = abs(df['price_change_3d'].iloc[position])
            if not pd.isna(momentum):
                momentum_factor = min(0.1, momentum * 5)  # Scale to max 0.1
        
        # Combine factors
        confidence = base_confidence + vol_factor + trend_factor + momentum_factor
        
        # Ensure confidence is between 0.0 and 1.0
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
        
    except Exception:
        return base_confidence


def get_latest_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """
    Extract latest indicator values for output
    
    Args:
        df: DataFrame with calculated indicators
        
    Returns:
        Dictionary with latest indicator values
    """
    if df.empty:
        return {}
    
    latest_indicators = {}
    
    # Get latest values for key indicators
    indicator_columns = ['ma', 'vol_avg', 'price_ma_ratio', 'volume_ratio', 'ma_slope']
    
    for col in indicator_columns:
        if col in df.columns and not df[col].empty:
            latest_value = df[col].iloc[-1]
            if not pd.isna(latest_value):
                latest_indicators[col] = float(latest_value)
    
    # Add basic OHLCV data
    basic_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in basic_columns:
        if col in df.columns:
            latest_indicators[col] = float(df[col].iloc[-1])
    
    return latest_indicators


def get_rule_description(rule_number: int) -> str:
    """
    Get description for a specific Granville rule
    
    Args:
        rule_number: Rule number (1-8)
        
    Returns:
        Rule description string
    """
    try:
        descriptions = get_rule_descriptions()
        return descriptions.get(rule_number, f"Unknown rule: {rule_number}")
    except Exception:
        return f"Rule {rule_number}" 