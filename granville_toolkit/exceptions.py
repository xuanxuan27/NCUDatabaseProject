"""
Custom exceptions for Granville Toolkit
"""


class GranvilleToolkitError(Exception):
    """Base exception for Granville Toolkit"""
    pass


class DataValidationError(GranvilleToolkitError):
    """Raised when input data validation fails"""
    pass


class IndicatorCalculationError(GranvilleToolkitError):
    """Raised when indicator calculation fails"""
    pass


class InsufficientDataError(GranvilleToolkitError):
    """Raised when there is insufficient data for calculation"""
    pass 