"""
Core Package for Granville Eight Rules Technical Analysis

This package provides simplified core functionality for technical analysis
based on Granville's Eight Rules.

Main Components:
- data_processor: Data validation and processing
- signal_processor: Technical indicator calculation and signal generation
- output_processor: Result formatting and API response creation
- main_api: Main entry point for analysis

Example Usage:
    from core import analyze_stock, SignalConfig
    
    response = analyze_stock("2330", historical_data)
    if response.success:
        print(f"Generated {len(response.data.signals)} signals")
"""

# Import main API functions
from .main_api import (
    analyze_stock,
    quick_analysis,
    get_analysis_summary,
    export_results,
    validate_input_data,
    granville_analysis
)

# Import configuration classes
from .signal_processor import Signal, SignalConfig

# Import result data structures
from .output_processor import AnalysisResult, APIResponse

# Import utility functions
from .data_processor import (
    process_input_data,
    validate_and_clean_data,
    get_data_summary
)

from .signal_processor import (
    generate_signals,
    calculate_indicators,
    get_latest_indicators,
    get_rule_description
)

from .output_processor import (
    format_analysis_result,
    create_api_response,
    create_summary_report,
    to_dict,
    to_json
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Technical Analysis Team"
__description__ = "Granville Eight Rules Technical Analysis Core Package"

# Define what gets imported with "from core import *"
__all__ = [
    # Main API functions
    'analyze_stock',
    'quick_analysis', 
    'get_analysis_summary',
    'export_results',
    'validate_input_data',
    'granville_analysis',
    
    # Data structures
    'Signal',
    'SignalConfig',
    'AnalysisResult', 
    'APIResponse',
    
    # Core processing functions
    'process_input_data',
    'validate_and_clean_data',
    'generate_signals',
    'calculate_indicators',
    'format_analysis_result',
    'create_api_response',
    
    # Utility functions
    'get_data_summary',
    'get_latest_indicators',
    'get_rule_description',
    'create_summary_report',
    'to_dict',
    'to_json'
] 