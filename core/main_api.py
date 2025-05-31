"""
Main API Module

This module provides the main entry point for stock technical analysis,
integrating all core modules:
- data_processor: Data validation and processing
- signal_processor: Technical indicator calculation and signal generation  
- output_processor: Result formatting and API response creation
"""

import pandas as pd
import time
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Import core modules
from .data_processor import (
    process_input_data, 
    get_data_summary,
    DataValidationError
)
from .signal_processor import (
    generate_signals,
    calculate_indicators,
    get_latest_indicators,
    Signal,
    SignalConfig,
    SignalProcessingError
)
from .output_processor import (
    format_analysis_result,
    create_api_response,
    create_summary_report,
    to_dict,
    to_json,
    validate_output_format,
    AnalysisResult,
    APIResponse,
    OutputProcessingError
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_stock(
    stock_code: str,
    historical_data: pd.DataFrame,
    current_data: Optional[Dict[str, Any]] = None,
    config: Optional[SignalConfig] = None
) -> APIResponse:
    """
    Main entry point for single stock analysis
    
    This function integrates all core modules to provide complete technical analysis
    based on Granville Eight Rules.
    
    Args:
        stock_code: Stock symbol/code for identification
        historical_data: Historical OHLCV data with columns:
                        ['date', 'open', 'high', 'low', 'close', 'volume']
        current_data: Optional real-time data dict with keys:
                     {'price': float, 'volume': int, 'timestamp': datetime/str}
        config: Optional SignalConfig for customizing analysis parameters
        
    Returns:
        APIResponse object with analysis results or error information
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting analysis for stock: {stock_code}")
        
        # Step 1: Data Processing
        logger.info("Step 1: Processing input data...")
        processed_data = process_input_data(
            historical_df=historical_data,
            realtime_data=current_data,
            stock_code=stock_code
        )
        
        # Step 2: Signal Generation
        logger.info("Step 2: Generating signals...")
        signals = generate_signals(
            df=processed_data,
            config=config
        )
        
        # Step 3: Calculate indicators for output
        logger.info("Step 3: Calculating final indicators...")
        if config is None:
            config = SignalConfig()
        
        indicators_df = calculate_indicators(
            df=processed_data,
            ma_window=config.ma_period,
            vol_window=config.volume_period
        )
        
        # Step 4: Format results
        processing_time = time.time() - start_time
        logger.info("Step 4: Formatting results...")
        
        metadata = {
            'stock_code': stock_code,
            'processing_time': processing_time,
            'data_summary': get_data_summary(processed_data)
        }
        
        analysis_result = format_analysis_result(
            signals=signals,
            indicators=indicators_df,
            metadata=metadata
        )
        
        # Step 5: Create API response
        api_response = create_api_response(
            result=analysis_result,
            success=True,
            additional_metadata={
                'config_used': {
                    'ma_period': config.ma_period,
                    'volume_period': config.volume_period,
                    'divergence_threshold': config.divergence_threshold,
                    'signal_filter_enabled': config.enable_signal_filter
                }
            }
        )
        
        # Validate output format
        if not validate_output_format(api_response):
            logger.warning("Output format validation failed")
        
        logger.info(f"Analysis completed for {stock_code} in {processing_time:.3f}s with {len(signals)} signals")
        return api_response
        
    except DataValidationError as e:
        logger.error(f"Data validation error for {stock_code}: {str(e)}")
        return create_api_response(
            success=False,
            error_message=f"Data validation failed: {str(e)}",
            additional_metadata={'error_type': 'DataValidationError', 'stock_code': stock_code}
        )
        
    except SignalProcessingError as e:
        logger.error(f"Signal processing error for {stock_code}: {str(e)}")
        return create_api_response(
            success=False,
            error_message=f"Signal processing failed: {str(e)}",
            additional_metadata={'error_type': 'SignalProcessingError', 'stock_code': stock_code}
        )
        
    except OutputProcessingError as e:
        logger.error(f"Output processing error for {stock_code}: {str(e)}")
        return create_api_response(
            success=False,
            error_message=f"Output processing failed: {str(e)}",
            additional_metadata={'error_type': 'OutputProcessingError', 'stock_code': stock_code}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error analyzing {stock_code}: {str(e)}")
        return create_api_response(
            success=False,
            error_message=f"Analysis failed: {str(e)}",
            additional_metadata={'error_type': 'UnexpectedError', 'stock_code': stock_code}
        )


def quick_analysis(
    stock_code: str,
    historical_data: pd.DataFrame,
    ma_period: int = 20
) -> Dict[str, Any]:
    """
    Quick analysis with minimal configuration for simple use cases
    
    Args:
        stock_code: Stock symbol/code
        historical_data: Historical OHLCV data
        ma_period: Moving average period (default: 20)
        
    Returns:
        Dictionary with simplified analysis results
    """
    try:
        config = SignalConfig(ma_period=ma_period, enable_signal_filter=False)
        response = analyze_stock(stock_code, historical_data, config=config)
        
        if response.success and response.data:
            return {
                'stock_code': response.data.stock_code,
                'signals': len(response.data.signals),
                'buy_signals': len([s for s in response.data.signals if s.signal_type == "BUY"]),
                'sell_signals': len([s for s in response.data.signals if s.signal_type == "SELL"]),
                'latest_price': response.data.latest_indicators.get('close', 0.0),
                'latest_ma': response.data.latest_indicators.get('ma', 0.0),
                'processing_time': response.data.processing_time
            }
        else:
            return {'error': response.error_message}
            
    except Exception as e:
        return {'error': f"Quick analysis failed: {str(e)}"}


def get_analysis_summary(response: APIResponse) -> Dict[str, Any]:
    """
    Get a summary of analysis results
    
    Args:
        response: APIResponse from analyze_stock()
        
    Returns:
        Summary dictionary
    """
    try:
        if response.success and response.data:
            return create_summary_report(response.data)
        else:
            return {'error': response.error_message}
    except Exception as e:
        return {'error': f"Summary creation failed: {str(e)}"}


def export_results(response: APIResponse, format_type: str = 'dict') -> Any:
    """
    Export analysis results in various formats
    
    Args:
        response: APIResponse from analyze_stock()
        format_type: 'dict' or 'json'
        
    Returns:
        Formatted results
    """
    try:
        if format_type.lower() == 'json':
            return to_json(response)
        else:
            return to_dict(response)
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return {'error': f"Export failed: {str(e)}"}


def validate_input_data(
    historical_data: pd.DataFrame,
    current_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate input data format before analysis
    
    Args:
        historical_data: Historical OHLCV DataFrame
        current_data: Optional real-time data
        
    Returns:
        Validation result dictionary
    """
    try:
        # Basic validation
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in historical_data.columns]
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'data_info': {}
        }
        
        if missing_columns:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required columns: {missing_columns}")
        
        if historical_data.empty:
            validation_result['valid'] = False
            validation_result['errors'].append("Historical data is empty")
        
        if len(historical_data) < 20:
            validation_result['warnings'].append("Limited historical data (< 20 rows)")
        
        # Data info
        if not historical_data.empty:
            validation_result['data_info'] = {
                'rows': len(historical_data),
                'date_range': {
                    'start': str(historical_data['date'].min()) if 'date' in historical_data.columns else 'N/A',
                    'end': str(historical_data['date'].max()) if 'date' in historical_data.columns else 'N/A'
                }
            }
        
        # Validate current_data if provided
        if current_data:
            if 'price' not in current_data:
                validation_result['warnings'].append("Current data missing 'price' field")
            elif current_data['price'] <= 0:
                validation_result['warnings'].append("Invalid current price value")
        
        return validation_result
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Validation failed: {str(e)}"],
            'warnings': [],
            'data_info': {}
        }


# Convenience function for backward compatibility
def granville_analysis(
    stock_code: str,
    historical_data: pd.DataFrame,
    **kwargs
) -> APIResponse:
    """
    Convenience function for Granville Eight Rules analysis
    
    Args:
        stock_code: Stock symbol/code
        historical_data: Historical OHLCV data
        **kwargs: Additional arguments for analyze_stock()
        
    Returns:
        APIResponse with analysis results
    """
    return analyze_stock(stock_code, historical_data, **kwargs)


if __name__ == "__main__":
    # Example usage
    print("Granville Technical Analysis Service")
    print("====================================")
    
    # This would typically be called by other services/applications
    # Example:
    # response = analyze_stock("2330", historical_df, current_data)
    # summary = get_analysis_summary(response)
    # print(to_json(summary, indent=2)) 