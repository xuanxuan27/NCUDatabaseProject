"""
Granville Eight Rules Technical Indicator Toolkit

A comprehensive toolkit for calculating technical indicators 
specifically designed for Granville's Eight Rules trading strategy.
"""

__version__ = "0.1.0"

from .indicators import (
    moving_average,
    volume_average,
    crossover_signal,
    breakout_signal
)

from .granville_rules import (
    granville_eight_rules,
    get_rule_descriptions
)

# For backward compatibility
granville_rules = granville_eight_rules

__all__ = [
    'moving_average',
    'volume_average', 
    'crossover_signal',
    'breakout_signal',
    'granville_rules',
    'granville_eight_rules',
    'get_rule_descriptions'
] 