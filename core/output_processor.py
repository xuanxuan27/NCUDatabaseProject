"""
Output Processing Module

This module handles:
- Standardizing signal output format
- Creating API responses
- Basic error handling
- Unified response structure
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging
import json

# Import Signal from signal_processor
from .signal_processor import Signal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Analysis result data structure as defined in document.md"""
    stock_code: str
    signals: List[Signal]
    latest_indicators: Dict[str, float]
    processing_time: float
    timestamp: datetime


@dataclass 
class APIResponse:
    """API response data structure as defined in document.md"""
    success: bool
    data: Optional[AnalysisResult]
    error_message: str
    metadata: Dict[str, Any]


class OutputProcessingError(Exception):
    """Custom exception for output processing errors"""
    pass


def format_analysis_result(
    signals: List[Signal], 
    indicators: pd.DataFrame,
    metadata: Dict[str, Any]
) -> AnalysisResult:
    """
    Format analysis results into standardized structure
    
    Args:
        signals: List of generated signals
        indicators: DataFrame with calculated indicators
        metadata: Additional metadata including stock_code, processing_time
        
    Returns:
        Formatted AnalysisResult object
    """
    try:
        # Extract latest indicators
        latest_indicators = _extract_latest_indicators(indicators)
        
        # Get metadata values
        stock_code = metadata.get('stock_code', 'UNKNOWN')
        processing_time = metadata.get('processing_time', 0.0)
        
        # Update signal stock codes if needed
        updated_signals = _update_signal_stock_codes(signals, stock_code)
        
        result = AnalysisResult(
            stock_code=stock_code,
            signals=updated_signals,
            latest_indicators=latest_indicators,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
        logger.info(f"Formatted analysis result for {stock_code}: {len(signals)} signals")
        return result
        
    except Exception as e:
        logger.error(f"Error formatting analysis result: {str(e)}")
        raise OutputProcessingError(f"Result formatting failed: {str(e)}")


def create_api_response(
    result: Optional[AnalysisResult] = None, 
    success: bool = True,
    error_message: str = "",
    additional_metadata: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """
    Create standardized API response
    
    Args:
        result: Analysis result object (None if error)
        success: Whether the operation was successful
        error_message: Error message if success=False
        additional_metadata: Additional metadata to include
        
    Returns:
        Formatted APIResponse object
    """
    try:
        # Build metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        if success and result:
            metadata.update({
                "signal_count": len(result.signals),
                "processing_time_ms": result.processing_time * 1000,
                "stock_code": result.stock_code
            })
        
        response = APIResponse(
            success=success,
            data=result,
            error_message=error_message,
            metadata=metadata
        )
        
        logger.info(f"Created API response: success={success}, signals={len(result.signals) if result else 0}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating API response: {str(e)}")
        # Return error response
        return APIResponse(
            success=False,
            data=None,
            error_message=f"Response creation failed: {str(e)}",
            metadata={"timestamp": datetime.now().isoformat(), "version": "1.0"}
        )


def to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert analysis objects to dictionary format
    
    Args:
        obj: Object to convert (AnalysisResult, APIResponse, or Signal)
        
    Returns:
        Dictionary representation
    """
    try:
        if isinstance(obj, (AnalysisResult, APIResponse, Signal)):
            result = asdict(obj)
            
            # Convert datetime objects to ISO format strings
            result = _convert_datetimes_to_strings(result)
            
            return result
        else:
            logger.warning(f"Unexpected object type for conversion: {type(obj)}")
            return {"error": f"Cannot convert object of type {type(obj)}"}
            
    except Exception as e:
        logger.error(f"Error converting object to dict: {str(e)}")
        return {"error": f"Conversion failed: {str(e)}"}


def to_json(obj: Any, indent: int = 2) -> str:
    """
    Convert analysis objects to JSON string
    
    Args:
        obj: Object to convert
        indent: JSON indentation level
        
    Returns:
        JSON string representation
    """
    try:
        dict_obj = to_dict(obj)
        return json.dumps(dict_obj, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error converting to JSON: {str(e)}")
        return json.dumps({"error": f"JSON conversion failed: {str(e)}"}, indent=indent)


def create_summary_report(result: AnalysisResult) -> Dict[str, Any]:
    """
    Create a summary report of the analysis
    
    Args:
        result: Analysis result object
        
    Returns:
        Summary report dictionary
    """
    try:
        # Signal summary
        buy_signals = [s for s in result.signals if s.signal_type == "BUY"]
        sell_signals = [s for s in result.signals if s.signal_type == "SELL"]
        
        # Confidence statistics
        confidences = [s.confidence for s in result.signals]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        max_confidence = max(confidences) if confidences else 0.0
        
        # Rule distribution
        rule_counts = {}
        for signal in result.signals:
            rule_counts[signal.rule_number] = rule_counts.get(signal.rule_number, 0) + 1
        
        summary = {
            "stock_code": result.stock_code,
            "analysis_timestamp": result.timestamp.isoformat(),
            "processing_time_ms": result.processing_time * 1000,
            "signal_summary": {
                "total_signals": len(result.signals),
                "buy_signals": len(buy_signals),
                "sell_signals": len(sell_signals),
                "avg_confidence": round(avg_confidence, 3),
                "max_confidence": round(max_confidence, 3)
            },
            "rule_distribution": rule_counts,
            "latest_price": result.latest_indicators.get('close', 0.0),
            "latest_ma": result.latest_indicators.get('ma', 0.0),
            "price_ma_ratio": result.latest_indicators.get('price_ma_ratio', 0.0)
        }
        
        logger.info(f"Created summary report for {result.stock_code}")
        return summary
        
    except Exception as e:
        logger.error(f"Error creating summary report: {str(e)}")
        return {"error": f"Summary creation failed: {str(e)}"}


def _extract_latest_indicators(indicators: pd.DataFrame) -> Dict[str, float]:
    """
    Extract latest indicator values from DataFrame
    
    Args:
        indicators: DataFrame with calculated indicators
        
    Returns:
        Dictionary with latest indicator values
    """
    if indicators.empty:
        return {}
    
    latest_indicators = {}
    
    # Key indicators to extract
    indicator_columns = [
        'close', 'open', 'high', 'low', 'volume',
        'ma', 'vol_avg', 'price_ma_ratio', 'volume_ratio', 'ma_slope'
    ]
    
    for col in indicator_columns:
        if col in indicators.columns:
            latest_value = indicators[col].iloc[-1]
            if pd.notna(latest_value):
                latest_indicators[col] = float(latest_value)
    
    return latest_indicators


def _update_signal_stock_codes(signals: List[Signal], stock_code: str) -> List[Signal]:
    """
    Update stock codes in signals if they are missing
    
    Args:
        signals: List of signals
        stock_code: Stock code to set
        
    Returns:
        Updated list of signals
    """
    updated_signals = []
    
    for signal in signals:
        if signal.stock_code == "UNKNOWN" or not signal.stock_code:
            # Create new signal with updated stock code
            updated_signal = Signal(
                stock_code=stock_code,
                rule_number=signal.rule_number,
                signal_type=signal.signal_type,
                timestamp=signal.timestamp,
                price=signal.price,
                confidence=signal.confidence
            )
            updated_signals.append(updated_signal)
        else:
            updated_signals.append(signal)
    
    return updated_signals


def _convert_datetimes_to_strings(obj: Any) -> Any:
    """
    Recursively convert datetime objects to ISO format strings
    
    Args:
        obj: Object to process
        
    Returns:
        Object with datetimes converted to strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_datetimes_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetimes_to_strings(item) for item in obj]
    else:
        return obj


def validate_output_format(response: APIResponse) -> bool:
    """
    Validate that the output response meets format requirements
    
    Args:
        response: API response to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        if not hasattr(response, 'success'):
            logger.error("Missing 'success' field")
            return False
        
        if not hasattr(response, 'metadata'):
            logger.error("Missing 'metadata' field")
            return False
        
        # If successful, check data structure
        if response.success and response.data:
            if not hasattr(response.data, 'stock_code'):
                logger.error("Missing 'stock_code' in data")
                return False
            
            if not hasattr(response.data, 'signals'):
                logger.error("Missing 'signals' in data")
                return False
        
        logger.info("Output format validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Output validation error: {str(e)}")
        return False 