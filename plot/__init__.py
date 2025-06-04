"""
Plotting Toolkit for Stock Charts and Technical Analysis

A comprehensive toolkit for generating various stock charts 
and technical indicators, including Candlestick + Volume, 
Bollinger Bands, RSI, KD, Granville Rules, Cross Signals, and Breakout Signals.
"""

__version__ = "0.1.0"

from .plot_figure import (
    plot_candle_and_volume_chart,
    plot_bollinger,
    plot_rsi,
    plot_kd,
    plot_all_charts,
    plot_granville_charts,
    plot_cross_chart,
    plot_breakout_chart,
)

__all__ = [
    'plot_candle_and_volume_chart',
    'plot_bollinger',
    'plot_rsi',
    'plot_kd',
    'plot_all_charts',
    'plot_granville_charts',
    'plot_cross_chart',
    'plot_breakout_chart',
]
