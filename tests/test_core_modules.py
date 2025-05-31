"""
Test script for core modules MVP version

This script tests the basic functionality of all 4 core modules:
- data_processor
- signal_processor 
- output_processor
- main_api
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core modules
try:
    from core import (
        analyze_stock, 
        quick_analysis, 
        validate_input_data,
        process_input_data, 
        validate_and_clean_data,
        generate_signals, 
        SignalConfig,
        create_api_response, 
        to_json
    )
    print("✅ All core modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_sample_data(days: int = 50) -> pd.DataFrame:
    """Create sample historical data for testing"""
    
    start_date = datetime.now() - timedelta(days=days)
    dates = pd.date_range(start=start_date, periods=days, freq='D')
    
    # Generate realistic stock price data
    np.random.seed(42)  # For reproducible results
    base_price = 100.0
    prices = [base_price]
    
    for i in range(1, days):
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))  # Ensure positive prices
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = prices[i-1] if i > 0 else price
        volume = int(np.random.uniform(1000000, 10000000))
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    return pd.DataFrame(data)


def test_data_processor():
    """Test data_processor module"""
    print("\n🧪 Testing data_processor module...")
    
    try:
        # Test 1: Basic data processing
        sample_data = create_sample_data(30)
        processed_data = process_input_data(sample_data, stock_code="TEST001")
        
        assert not processed_data.empty
        assert all(col in processed_data.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume'])
        print("✅ Basic data processing: PASSED")
        
        # Test 2: Real-time data merge
        current_data = {
            'price': 105.5,
            'volume': 1500000,
            'timestamp': datetime.now()
        }
        merged_data = process_input_data(sample_data, current_data, "TEST001")
        assert len(merged_data) >= len(sample_data)
        print("✅ Real-time data merge: PASSED")
        
        # Test 3: Data validation
        validated_data = validate_and_clean_data(sample_data)
        assert not validated_data.empty
        print("✅ Data validation: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processor test failed: {e}")
        return False


def test_signal_processor():
    """Test signal_processor module"""
    print("\n🧪 Testing signal_processor module...")
    
    try:
        # Test 1: Signal generation
        sample_data = create_sample_data(40)
        processed_data = process_input_data(sample_data, stock_code="TEST002")
        
        config = SignalConfig(ma_period=20, volume_period=5)
        signals = generate_signals(processed_data, config)
        
        print(f"✅ Signal generation: PASSED ({len(signals)} signals generated)")
        
        # Test 2: Different configurations
        config2 = SignalConfig(ma_period=10, enable_signal_filter=False)
        signals2 = generate_signals(processed_data, config2)
        
        print(f"✅ Different config: PASSED ({len(signals2)} signals generated)")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal processor test failed: {e}")
        return False


def test_output_processor():
    """Test output_processor module"""
    print("\n🧪 Testing output_processor module...")
    
    try:
        # Test 1: API response creation
        response = create_api_response(
            result=None,
            success=True,
            additional_metadata={'test': True}
        )
        
        assert hasattr(response, 'success')
        assert hasattr(response, 'metadata')
        print("✅ API response creation: PASSED")
        
        # Test 2: JSON conversion
        json_output = to_json(response)
        assert isinstance(json_output, str)
        assert 'success' in json_output
        print("✅ JSON conversion: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Output processor test failed: {e}")
        return False


def test_main_api():
    """Test main_api module"""
    print("\n🧪 Testing main_api module...")
    
    try:
        # Test 1: Input validation
        sample_data = create_sample_data(35)
        validation_result = validate_input_data(sample_data)
        
        assert validation_result['valid'] == True
        print("✅ Input validation: PASSED")
        
        # Test 2: Quick analysis
        quick_result = quick_analysis("TEST003", sample_data, ma_period=15)
        
        assert 'stock_code' in quick_result
        assert 'signals' in quick_result
        print(f"✅ Quick analysis: PASSED ({quick_result.get('signals', 0)} signals)")
        
        # Test 3: Full analysis
        response = analyze_stock("TEST004", sample_data)
        
        assert response.success
        assert response.data is not None
        print(f"✅ Full analysis: PASSED ({len(response.data.signals)} signals)")
        
        # Test 4: Analysis with real-time data
        current_data = {'price': 102.3, 'volume': 2000000}
        response_rt = analyze_stock("TEST005", sample_data, current_data)
        
        assert response_rt.success
        print("✅ Real-time analysis: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Main API test failed: {e}")
        return False


def test_integration():
    """Test integration between all modules"""
    print("\n🧪 Testing module integration...")
    
    try:
        # Create realistic test scenario
        sample_data = create_sample_data(60)
        
        # Configure analysis
        config = SignalConfig(
            ma_period=20,
            volume_period=5,
            divergence_threshold=2.5,
            enable_signal_filter=True
        )
        
        current_data = {
            'price': sample_data['close'].iloc[-1] * 1.02,  # 2% higher than last close
            'volume': int(sample_data['volume'].mean() * 1.5),  # 50% higher volume
            'timestamp': datetime.now()
        }
        
        # Perform full analysis
        response = analyze_stock(
            stock_code="INTEGRATION_TEST",
            historical_data=sample_data,
            current_data=current_data,
            config=config
        )
        
        # Verify response structure
        assert response.success
        assert response.data is not None
        assert response.data.stock_code == "INTEGRATION_TEST"
        assert isinstance(response.data.signals, list)
        assert isinstance(response.data.latest_indicators, dict)
        assert response.data.processing_time > 0
        
        # Test export functionality
        dict_export = to_json(response)
        assert isinstance(dict_export, str)
        
        print(f"✅ Integration test: PASSED")
        print(f"   - Signals generated: {len(response.data.signals)}")
        print(f"   - Processing time: {response.data.processing_time:.3f}s")
        print(f"   - Latest price: {response.data.latest_indicators.get('close', 'N/A')}")
        print(f"   - Latest MA: {response.data.latest_indicators.get('ma', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Core Modules MVP Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run individual module tests
    test_results.append(("Data Processor", test_data_processor()))
    test_results.append(("Signal Processor", test_signal_processor()))
    test_results.append(("Output Processor", test_output_processor()))
    test_results.append(("Main API", test_main_api()))
    test_results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MVP core modules are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 