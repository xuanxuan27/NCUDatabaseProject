"""
Example Usage of Core Modules

This example demonstrates how to use the simplified core modules
for Granville Eight Rules technical analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main API
from core import (
    analyze_stock, 
    quick_analysis, 
    get_analysis_summary, 
    export_results,
    SignalConfig,
    to_json
)


def create_sample_stock_data(symbol: str = "2330", days: int = 60) -> pd.DataFrame:
    """Create realistic sample stock data for demonstration"""
    
    print(f"📊 Creating sample data for {symbol} ({days} days)")
    
    start_date = datetime.now() - timedelta(days=days)
    dates = pd.date_range(start=start_date, periods=days, freq='D')
    
    # Generate realistic Taiwan stock price movements
    np.random.seed(42)
    base_price = 550.0 if symbol == "2330" else 100.0  # TSM-like price
    prices = [base_price]
    
    for i in range(1, days):
        # Taiwan stock market characteristics
        change = np.random.normal(0, 0.025)  # 2.5% daily volatility
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 10.0))  # Minimum price
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        daily_volatility = abs(np.random.normal(0, 0.015))
        high = price * (1 + daily_volatility)
        low = price * (1 - daily_volatility)
        open_price = prices[i-1] * (1 + np.random.normal(0, 0.005)) if i > 0 else price
        
        # Taiwan stock typical volume (in thousands)
        base_volume = 25000 if symbol == "2330" else 5000
        volume = int(base_volume * (1 + abs(np.random.normal(0, 0.5))) * 1000)
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(price, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    print(f"✅ Generated data: {len(df)} rows, price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    return df


def example_1_basic_analysis():
    """Example 1: Basic stock analysis with default settings"""
    
    print("\n" + "="*60)
    print("📈 Example 1: Basic Analysis (Default Settings)")
    print("="*60)
    
    # Create sample data
    stock_data = create_sample_stock_data("2330", 45)
    
    # Perform basic analysis
    print("\n🔍 Performing basic analysis...")
    response = analyze_stock(
        stock_code="2330",
        historical_data=stock_data
    )
    
    # Display results
    if response.success:
        print(f"✅ Analysis successful!")
        print(f"   📊 Signals generated: {len(response.data.signals)}")
        print(f"   ⏱️  Processing time: {response.data.processing_time:.3f}s")
        print(f"   💰 Latest price: NT${response.data.latest_indicators.get('close', 0):.2f}")
        print(f"   📈 20-day MA: NT${response.data.latest_indicators.get('ma', 0):.2f}")
        
        # Show signals
        for signal in response.data.signals:
            print(f"   🚨 Signal: {signal.signal_type} (Rule {signal.rule_number}) - Confidence: {signal.confidence:.2%}")
    else:
        print(f"❌ Analysis failed: {response.error_message}")


def example_2_custom_configuration():
    """Example 2: Analysis with custom configuration"""
    
    print("\n" + "="*60)
    print("📈 Example 2: Custom Configuration")
    print("="*60)
    
    # Create sample data
    stock_data = create_sample_stock_data("3008", 30)
    
    # Custom configuration
    custom_config = SignalConfig(
        ma_period=10,           # Shorter MA for more sensitive signals
        volume_period=3,        # Shorter volume period
        divergence_threshold=2.0,  # Lower threshold for more signals
        enable_signal_filter=True
    )
    
    print("\n🛠️  Using custom configuration:")
    print(f"   📊 MA Period: {custom_config.ma_period} days")
    print(f"   📈 Volume Period: {custom_config.volume_period} days")
    print(f"   🎯 Divergence Threshold: {custom_config.divergence_threshold}%")
    
    # Perform analysis
    print("\n🔍 Performing custom analysis...")
    response = analyze_stock(
        stock_code="3008",
        historical_data=stock_data,
        config=custom_config
    )
    
    # Show detailed summary
    if response.success:
        summary = get_analysis_summary(response)
        print(f"✅ Analysis successful!")
        print(f"   📊 Total signals: {summary['signal_summary']['total_signals']}")
        print(f"   🟢 Buy signals: {summary['signal_summary']['buy_signals']}")
        print(f"   🔴 Sell signals: {summary['signal_summary']['sell_signals']}")
        print(f"   🎯 Average confidence: {summary['signal_summary']['avg_confidence']:.1%}")


def example_3_realtime_analysis():
    """Example 3: Analysis with real-time data"""
    
    print("\n" + "="*60)
    print("📈 Example 3: Real-time Data Analysis")
    print("="*60)
    
    # Create sample historical data
    stock_data = create_sample_stock_data("2454", 50)
    
    # Simulate real-time data
    last_close = stock_data['close'].iloc[-1]
    current_data = {
        'price': last_close * 1.025,  # 2.5% higher than yesterday
        'volume': 15000000,           # High volume
        'timestamp': datetime.now()
    }
    
    print(f"\n📡 Real-time data:")
    print(f"   💰 Current price: NT${current_data['price']:.2f} (+2.5%)")
    print(f"   📈 Volume: {current_data['volume']:,}")
    print(f"   🕐 Timestamp: {current_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Perform analysis with real-time data
    print("\n🔍 Performing real-time analysis...")
    response = analyze_stock(
        stock_code="2454",
        historical_data=stock_data,
        current_data=current_data
    )
    
    if response.success:
        print(f"✅ Real-time analysis successful!")
        
        # Export results in JSON format
        json_results = export_results(response, format_type='json')
        
        # Display key insights
        print(f"   📊 Signals detected: {len(response.data.signals)}")
        if response.data.signals:
            latest_signal = response.data.signals[-1]
            print(f"   🚨 Latest signal: {latest_signal.signal_type} (Rule {latest_signal.rule_number})")
            print(f"   🎯 Signal confidence: {latest_signal.confidence:.1%}")
        
        print(f"   📈 Price/MA ratio: {response.data.latest_indicators.get('price_ma_ratio', 1):.3f}")
        print(f"   📊 Volume ratio: {response.data.latest_indicators.get('volume_ratio', 1):.2f}")


def example_4_quick_analysis():
    """Example 4: Quick analysis for simple use cases"""
    
    print("\n" + "="*60)
    print("📈 Example 4: Quick Analysis")
    print("="*60)
    
    # Create sample data for multiple stocks
    stocks = ["2330", "2317", "2454"]
    
    print("🚀 Performing quick analysis for multiple stocks...")
    
    for stock in stocks:
        stock_data = create_sample_stock_data(stock, 35)
        
        # Quick analysis with 15-day MA
        result = quick_analysis(stock, stock_data, ma_period=15)
        
        if 'error' not in result:
            print(f"\n📊 {stock}:")
            print(f"   🎯 Signals: {result['signals']} (Buy: {result['buy_signals']}, Sell: {result['sell_signals']})")
            print(f"   💰 Price: NT${result['latest_price']:.2f}")
            print(f"   📈 15-day MA: NT${result['latest_ma']:.2f}")
            print(f"   ⏱️  Processing: {result['processing_time']*1000:.1f}ms")
        else:
            print(f"❌ {stock}: {result['error']}")


def main():
    """Run all examples"""
    
    print("🎯 Granville Eight Rules - Core Modules Examples")
    print("=" * 60)
    print("This demonstration shows how to use the simplified core modules")
    print("for technical analysis based on Granville's Eight Rules.")
    
    try:
        # Run examples
        example_1_basic_analysis()
        example_2_custom_configuration()
        example_3_realtime_analysis()
        example_4_quick_analysis()
        
        print("\n" + "="*60)
        print("🎉 All examples completed successfully!")
        print("\n📝 Key Features Demonstrated:")
        print("   ✅ Basic stock analysis with default settings")
        print("   ✅ Custom configuration for different trading styles")
        print("   ✅ Real-time data integration")
        print("   ✅ Quick analysis for multiple stocks")
        print("   ✅ JSON export capabilities")
        print("   ✅ Detailed signal information and confidence scores")
        
        print("\n🚀 Ready for production integration!")
        
    except Exception as e:
        print(f"❌ Error during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 