"""
Test script for Granville Toolkit
"""

import pandas as pd
import numpy as np
import granville_toolkit as gt

# Create sample OHLCV data for testing
def create_sample_data(days=100):
    """Create sample stock data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    base_price = 100
    
    # Generate realistic price movements
    returns = np.random.normal(0.001, 0.02, days)
    prices = [base_price]
    
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    # Create OHLCV data
    close_prices = np.array(prices)
    high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]
    
    volumes = np.random.normal(1000000, 200000, days)
    volumes = np.abs(volumes).astype(int)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })
    
    return df

def test_toolkit():
    """Test all toolkit functions"""
    print("Creating sample data...")
    df = create_sample_data()
    
    print("Testing moving_average function...")
    # Test SMA
    df = gt.moving_average(df, window=20, column='close', ma_type='sma', out_col='ma20')
    print(f"✓ SMA calculated, sample values: {df['ma20'].dropna().head(3).values}")
    
    # Test EMA
    df = gt.moving_average(df, window=10, column='close', ma_type='ema', out_col='ema10')
    print(f"✓ EMA calculated, sample values: {df['ema10'].dropna().head(3).values}")
    
    print("\nTesting volume_average function...")
    df = gt.volume_average(df, window=5, out_col='vol_ma5')
    print(f"✓ Volume MA calculated, sample values: {df['vol_ma5'].dropna().head(3).values}")
    
    print("\nTesting crossover_signal function...")
    # Add short MA for crossover test
    df = gt.moving_average(df, window=5, column='close', ma_type='sma', out_col='ma5')
    df = gt.crossover_signal(df, short_col='ma5', long_col='ma20', out_col='golden_cross')
    crossover_signals = df['golden_cross'].value_counts()
    print(f"✓ Crossover signals calculated: {crossover_signals.to_dict()}")
    
    print("\nTesting breakout_signal function...")
    df = gt.breakout_signal(df, price_col='close', ma_col='ma20', out_col='breakout')
    breakout_signals = df['breakout'].value_counts()
    print(f"✓ Breakout signals calculated: {breakout_signals.to_dict()}")
    
    print("\nTesting granville_eight_rules function...")
    df = gt.granville_eight_rules(
        df, 
        ma_col='ma20', 
        price_col='close', 
        vol_col='volume',
        vol_ma_col='vol_ma5',
        out_col='granville_signal'
    )
    granville_signals = df['granville_signal'].value_counts().sort_index()
    print(f"✓ Granville Eight Rules signals calculated: {granville_signals.to_dict()}")
    
    # Display rule descriptions
    print("\n📖 Granville Eight Rules descriptions:")
    rule_descriptions = gt.get_rule_descriptions()
    for rule_num, description in rule_descriptions.items():
        count = (df['granville_signal'] == rule_num).sum()
        print(f"Rule {rule_num}: {description} (觸發次數: {count})")
    
    print("\nTesting KD and RSI indicators...")
    # Test RSI
    df = gt.calculate_rsi(df, period=14, out_col='RSI')
    print(f"✓ RSI calculated, sample values: {df['RSI'].dropna().head(3).values}")
    # Test KD
    df = gt.calculate_kd(df, n=9, m1=3, m2=3, out_k='K', out_d='D')
    print(f"✓ KD calculated, sample K values: {df['K'].dropna().head(3).values}")
    print(f"✓ KD calculated, sample D values: {df['D'].dropna().head(3).values}")
    
    print("\nDisplaying sample results:")
    display_cols = ['date', 'close', 'ma5', 'ma20', 'volume', 'vol_ma5', 
                   'golden_cross', 'breakout', 'granville_signal', 'RSI', 'K', 'D']
    print(df[display_cols].tail(10))
    
    # Show specific Granville signals
    granville_triggered = df[df['granville_signal'] > 0]
    if len(granville_triggered) > 0:
        print(f"\n🎯 Granville signals triggered ({len(granville_triggered)} total):")
        print(granville_triggered[['date', 'close', 'ma20', 'granville_signal']].head())
    else:
        print("\n🎯 No Granville signals triggered in this sample data")
    
    print("\n✅ All tests completed successfully!")
    return df

def test_granville_rules_detailed():
    """Test Granville rules with more detailed analysis"""
    print("\n" + "="*60)
    print("🔍 DETAILED GRANVILLE RULES ANALYSIS")
    print("="*60)
    
    # Create more volatile sample data to trigger more signals
    np.random.seed(123)  # Different seed for more signals
    
    dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
    base_price = 100
    
    # Create more dramatic price movements
    returns = np.random.normal(0.002, 0.03, 200)
    prices = [base_price]
    
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    close_prices = np.array(prices)
    volumes = np.random.normal(1000000, 400000, 200)
    volumes = np.abs(volumes).astype(int)
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volumes,
        'open': close_prices,
        'high': close_prices * 1.01,
        'low': close_prices * 0.99
    })
    
    # Calculate indicators
    df = gt.moving_average(df, window=20, column='close', out_col='ma20')
    df = gt.volume_average(df, window=5, out_col='vol_ma5')
    
    # Apply Granville rules
    df = gt.granville_eight_rules(df, out_col='granville_signal')
    
    # Analyze results
    granville_counts = df['granville_signal'].value_counts().sort_index()
    print("📊 Granville Rules Signal Distribution:")
    
    rule_descriptions = gt.get_rule_descriptions()
    for rule_num in range(1, 9):
        count = granville_counts.get(rule_num, 0)
        rule_type = "買進" if rule_num <= 4 else "賣出"
        description = rule_descriptions[rule_num]
        print(f"  Rule {rule_num} ({rule_type}): {count} 次 - {description}")
    
    total_signals = (df['granville_signal'] > 0).sum()
    print(f"\n📈 總訊號數: {total_signals}")
    print(f"📊 訊號密度: {total_signals/len(df)*100:.1f}%")
    
    return df

if __name__ == "__main__":
    print("🚀 Starting Granville Toolkit Tests...")
    test_results = test_toolkit()
    
    # Run detailed analysis
    detailed_results = test_granville_rules_detailed()
    
    print("\n🎉 All tests completed successfully!") 