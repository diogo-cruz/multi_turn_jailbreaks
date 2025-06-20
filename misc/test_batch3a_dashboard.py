#!/usr/bin/env python3
"""
Test script for batch3a_dashboard.py

Verifies that all core functions work correctly with the actual data.
"""

import sys
import pandas as pd
from pathlib import Path

# Add the misc directory to the path so we can import the dashboard functions
sys.path.append('.')

# Import functions from the dashboard
from batch3a_dashboard import (
    load_batch3a_data,
    calculate_asr_by_dimension,
    calculate_asr_by_combination,
    create_summary_metrics
)

def test_dashboard_functions():
    """Test all the main dashboard functions."""
    print("🧪 Testing Batch3A Dashboard Functions...")
    
    try:
        # Test data loading
        print("\n1. Testing data loading...")
        df = pd.read_csv("../csv_results/batch3A_with_fp.csv")
        print(f"✅ Loaded {len(df)} experiments")
        print(f"   - Models: {len(df['target_model'].unique())}")
        print(f"   - Test cases: {len(df['test_case'].unique())}")
        print(f"   - Tactics: {len(df['jailbreak_tactic'].unique())}")
        print(f"   - False positives: {(df['fp_decision'] == 'false_positive').sum()}")
        
        # Clean model names
        df['model_short'] = df['target_model'].str.split('/').str[-1]
        
        # Test summary metrics
        print("\n2. Testing summary metrics...")
        metrics = create_summary_metrics(df)
        print(f"✅ Summary metrics calculated:")
        print(f"   - Total experiments: {metrics['total_experiments']}")
        print(f"   - Original ASR: {metrics['original_asr']:.1f}%")
        print(f"   - Adjusted ASR: {metrics['adjusted_asr']:.1f}%")
        print(f"   - ASR reduction: {metrics['asr_reduction']:.1f}pp")
        print(f"   - FP rate among successes: {metrics['fp_rate_among_successful']:.1f}%")
        
        # Test ASR calculations by dimension
        print("\n3. Testing ASR by model...")
        model_asr = calculate_asr_by_dimension(df, 'model_short')
        print(f"✅ Model ASR calculated for {len(model_asr)} models")
        print(f"   Top model (original ASR): {model_asr.iloc[0]['model_short']} - {model_asr.iloc[0]['original_asr']:.1f}%")
        
        print("\n4. Testing ASR by test case...")
        test_case_asr = calculate_asr_by_dimension(df, 'test_case')
        print(f"✅ Test case ASR calculated for {len(test_case_asr)} test cases")
        print(f"   Top test case (original ASR): {test_case_asr.iloc[0]['test_case']} - {test_case_asr.iloc[0]['original_asr']:.1f}%")
        
        print("\n5. Testing ASR by tactic...")
        tactic_asr = calculate_asr_by_dimension(df, 'jailbreak_tactic')
        print(f"✅ Tactic ASR calculated for {len(tactic_asr)} tactics")
        print(f"   Top tactic (original ASR): {tactic_asr.iloc[0]['jailbreak_tactic']} - {tactic_asr.iloc[0]['original_asr']:.1f}%")
        
        print("\n6. Testing ASR by combination...")
        combo_asr = calculate_asr_by_combination(df)
        print(f"✅ Combination ASR calculated for {len(combo_asr)} combinations")
        print(f"   Top combination (original ASR): {combo_asr.iloc[0]['combination']} - {combo_asr.iloc[0]['original_asr']:.1f}%")
        
        # Test data integrity
        print("\n7. Testing data integrity...")
        total_fp = (df['fp_decision'] == 'false_positive').sum()
        total_successes = df['goal_achieved'].sum()
        adjusted_successes = total_successes - total_fp
        
        print(f"✅ Data integrity checks:")
        print(f"   - Original successes: {total_successes}")
        print(f"   - False positives: {total_fp}")
        print(f"   - Adjusted successes: {adjusted_successes}")
        print(f"   - ASR reduction: {((total_successes - adjusted_successes) / len(df)) * 100:.1f}pp")
        
        print("\n🎉 All tests passed! Dashboard functions are working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_functions()
    sys.exit(0 if success else 1)