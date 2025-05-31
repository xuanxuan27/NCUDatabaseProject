"""
Data Processing Module

This module handles all data-related operations including:
- Input data validation and cleaning
- Historical and real-time data merging
- Data standardization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


def process_input_data(
    historical_df: pd.DataFrame, 
    realtime_data: Optional[dict] = None,
    stock_code: str = ""
) -> pd.DataFrame:
    """
    Process input data by validating, cleaning and merging historical with real-time data
    
    Args:
        historical_df: Historical OHLCV data
        realtime_data: Optional real-time data dict
        stock_code: Stock code for logging purposes
        
    Returns:
        Processed DataFrame ready for analysis
    """
    try:
        # Step 1: Validate and clean historical data
        logger.info(f"Processing data for stock: {stock_code}")
        cleaned_df = validate_and_clean_data(historical_df.copy())
        
        # Step 2: Merge with real-time data if provided
        if realtime_data:
            logger.info("Merging with real-time data")
            processed_df = merge_realtime_data(
                cleaned_df,
                realtime_data.get('price', 0),
                realtime_data.get('volume', 0),
                realtime_data.get('timestamp', datetime.now())
            )
        else:
            processed_df = cleaned_df
            
        logger.info(f"Data processing completed. Final shape: {processed_df.shape}")
        return processed_df
        
    except Exception as e:
        logger.error(f"Error processing data for {stock_code}: {str(e)}")
        raise DataValidationError(f"Data processing failed: {str(e)}")


def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate DataFrame format and clean the data
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned and validated DataFrame
        
    Raises:
        DataValidationError: If data validation fails
    """
    if df.empty:
        raise DataValidationError("Input DataFrame is empty")
    
    # Required columns check
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise DataValidationError(f"Missing required columns: {missing_columns}")
    
    # Create a copy to avoid modifying original data
    cleaned_df = df.copy()
    
    # Convert date column to datetime
    try:
        if not pd.api.types.is_datetime64_any_dtype(cleaned_df['date']):
            cleaned_df['date'] = pd.to_datetime(cleaned_df['date'])
    except Exception as e:
        raise DataValidationError(f"Date conversion failed: {str(e)}")
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        try:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        except Exception as e:
            raise DataValidationError(f"Numeric conversion failed for {col}: {str(e)}")
    
    # Basic data quality checks
    _perform_quality_checks(cleaned_df)
    
    # Handle missing values
    cleaned_df = _handle_missing_values(cleaned_df)
    
    # Sort by date
    cleaned_df = cleaned_df.sort_values('date').reset_index(drop=True)
    
    logger.info(f"Data validation completed. Shape: {cleaned_df.shape}")
    return cleaned_df


def merge_realtime_data(
    historical_df: pd.DataFrame, 
    current_price: float, 
    current_volume: int,
    timestamp: datetime
) -> pd.DataFrame:
    """
    Merge historical data with current real-time data
    
    Args:
        historical_df: Historical OHLCV data
        current_price: Current stock price
        current_volume: Current volume
        timestamp: Current timestamp
        
    Returns:
        DataFrame with updated current day data
    """
    if historical_df.empty:
        raise DataValidationError("Historical data is empty")
    
    if current_price <= 0:
        logger.warning("Invalid current price, skipping real-time merge")
        return historical_df
    
    merged_df = historical_df.copy()
    current_date = timestamp.date()
    
    # Check if we need to update today's data or create new row
    if not merged_df.empty:
        last_date = merged_df['date'].iloc[-1].date()
        
        if last_date == current_date:
            # Update today's data
            last_idx = len(merged_df) - 1
            merged_df.loc[last_idx, 'high'] = max(merged_df.loc[last_idx, 'high'], current_price)
            merged_df.loc[last_idx, 'low'] = min(merged_df.loc[last_idx, 'low'], current_price)
            merged_df.loc[last_idx, 'close'] = current_price
            merged_df.loc[last_idx, 'volume'] += current_volume
            logger.info(f"Updated today's data with price: {current_price}")
        else:
            # Create new row for today
            new_row = {
                'date': timestamp,
                'open': current_price,
                'high': current_price,
                'low': current_price,
                'close': current_price,
                'volume': current_volume
            }
            merged_df = pd.concat([merged_df, pd.DataFrame([new_row])], ignore_index=True)
            logger.info(f"Added new row for date: {current_date}")
    
    return merged_df


def _perform_quality_checks(df: pd.DataFrame) -> None:
    """
    Perform basic data quality checks
    
    Args:
        df: DataFrame to check
        
    Raises:
        DataValidationError: If quality checks fail
    """
    # Check for negative prices or volumes
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if (df[col] <= 0).any():
            raise DataValidationError(f"Found non-positive values in {col}")
    
    if (df['volume'] < 0).any():
        raise DataValidationError("Found negative volume values")
    
    # Check OHLC logic (High >= Low, etc.)
    invalid_ohlc = (
        (df['high'] < df['low']) |
        (df['high'] < df['open']) |
        (df['high'] < df['close']) |
        (df['low'] > df['open']) |
        (df['low'] > df['close'])
    )
    
    if invalid_ohlc.any():
        logger.warning(f"Found {invalid_ohlc.sum()} rows with invalid OHLC relationships")
    
    # Check for extreme price movements (more than 50% change)
    if len(df) > 1:
        price_change = abs(df['close'].pct_change())
        extreme_moves = price_change > 0.5
        if extreme_moves.any():
            logger.warning(f"Found {extreme_moves.sum()} extreme price movements (>50%)")


def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the dataset
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with missing values handled
    """
    # Check for missing values
    missing_counts = df.isnull().sum()
    
    if missing_counts.any():
        logger.warning(f"Missing values found: {missing_counts[missing_counts > 0].to_dict()}")
        
        # For price data, forward fill then backward fill
        price_columns = ['open', 'high', 'low', 'close']
        df[price_columns] = df[price_columns].fillna(method='ffill').fillna(method='bfill')
        
        # For volume, fill with 0
        df['volume'] = df['volume'].fillna(0)
        
        # Drop rows that still have missing values
        df = df.dropna()
        
        logger.info(f"After handling missing values, shape: {df.shape}")
    
    return df


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary statistics of the processed data
    
    Args:
        df: Processed DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {"error": "DataFrame is empty"}
    
    return {
        "total_rows": len(df),
        "date_range": {
            "start": df['date'].min().strftime('%Y-%m-%d'),
            "end": df['date'].max().strftime('%Y-%m-%d')
        },
        "price_range": {
            "min": float(df['low'].min()),
            "max": float(df['high'].max()),
            "latest": float(df['close'].iloc[-1])
        },
        "volume_stats": {
            "avg": float(df['volume'].mean()),
            "max": int(df['volume'].max()),
            "latest": int(df['volume'].iloc[-1])
        }
    } 