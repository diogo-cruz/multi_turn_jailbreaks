import pandas as pd
import json

# Load the CSV file
print("Loading CSV file...")
df = pd.read_csv("public/data/master_results.csv")

# Print basic info
print(f"DataFrame shape: {df.shape}")
print(f"Column names: {df.columns.tolist()}")

# Check the goal_achieved column
print("\nAnalyzing goal_achieved column:")
print(f"unique values: {df['goal_achieved'].unique()}")
print(f"value counts: \n{df['goal_achieved'].value_counts()}")
print(f"dtype: {df['goal_achieved'].dtype}")

# Check the first few rows in detail
print("\nFirst 5 rows:")
for i, row in df.head().iterrows():
    print(f"\nRow {i}:")
    print(f"  goal_achieved: {row['goal_achieved']} (type: {type(row['goal_achieved'])})")
    print(f"  turn_type: {row['turn_type']} (type: {type(row['turn_type'])})")
    print(f"  target_temp: {row['target_temp']} (type: {type(row['target_temp'])})")

# Count success rates by turn type
print("\nSuccess rates:")
single_count = len(df[df['turn_type'] == 'single'])
single_success = len(df[(df['turn_type'] == 'single') & (df['goal_achieved'] == True)])
multi_count = len(df[df['turn_type'] == 'multi'])
multi_success = len(df[(df['turn_type'] == 'multi') & (df['goal_achieved'] == True)])

print(f"Single-turn: {single_success}/{single_count} ({single_success/single_count*100:.2f}%)")
print(f"Multi-turn: {multi_success}/{multi_count} ({multi_success/multi_count*100:.2f}%)")

# Try different string comparisons
print("\nTrying different string comparisons:")
single_success_str = len(df[(df['turn_type'] == 'single') & (df['goal_achieved'].astype(str).str.lower() == 'true')])
multi_success_str = len(df[(df['turn_type'] == 'multi') & (df['goal_achieved'].astype(str).str.lower() == 'true')])

print(f"Single-turn (string 'true'): {single_success_str}/{single_count} ({single_success_str/single_count*100:.2f}%)")
print(f"Multi-turn (string 'true'): {multi_success_str}/{multi_count} ({multi_success_str/multi_count*100:.2f}%)")

# Check other possible values
for val in ['True', 'true', '1', 'yes', 'y']:
    single_val = len(df[(df['turn_type'] == 'single') & (df['goal_achieved'].astype(str).str.lower() == val.lower())])
    multi_val = len(df[(df['turn_type'] == 'multi') & (df['goal_achieved'].astype(str).str.lower() == val.lower())])
    print(f"Value '{val}': Single-turn: {single_val}, Multi-turn: {multi_val}")

# Verify ASR calculation with a test case
print("\n===== ASR CALCULATION TEST =====")

# Choose a specific model to check
test_model = "meta-llama/llama-3.1-70b-instruct"
model_df = df[df['target_model'] == test_model]
print(f"Testing model: {test_model} with {len(model_df)} rows")

# Check ASR calculation
# Group by test case and tactic, find max success rate for each test case
test_cases = model_df['test_case'].unique()
print(f"Found {len(test_cases)} test cases for {test_model}")

# Test both single and multi-turn ASR calculations
for turn_type in ['single', 'multi']:
    print(f"\n--- {turn_type.upper()}-TURN ASR ---")
    turn_df = model_df[model_df['turn_type'] == turn_type]
    print(f"Total {turn_type}-turn rows: {len(turn_df)}")
    
    test_case_max_rates = []
    
    for test_case in test_cases:
        test_case_df = turn_df[turn_df['test_case'] == test_case]
        if len(test_case_df) == 0:
            continue  # Skip if no data for this test case with this turn type
            
        print(f"\nTest case: {test_case} ({len(test_case_df)} rows)")
        
        # Group by tactic and calculate success rate
        tactic_rates = {}
        for tactic, tdf in test_case_df.groupby('jailbreak_tactic'):
            success_count = len(tdf[tdf['goal_achieved'] == True])
            success_rate = (success_count / len(tdf)) * 100 if len(tdf) > 0 else 0
            tactic_rates[tactic] = success_rate
            print(f"  Tactic: {tactic}: {success_count}/{len(tdf)} = {success_rate:.2f}%")
        
        if tactic_rates:
            max_rate = max(tactic_rates.values())
            max_tactic = max(tactic_rates.items(), key=lambda x: x[1])[0]
            test_case_max_rates.append(max_rate)
            print(f"  → Max rate: {max_rate:.2f}% (tactic: {max_tactic})")
    
    # Calculate average of maximums
    if test_case_max_rates:
        avg_asr = sum(test_case_max_rates) / len(test_case_max_rates)
        print(f"\n{turn_type.upper()}-TURN ASR = {avg_asr:.2f}% (average of {len(test_case_max_rates)} max rates)")
    else:
        print(f"\nNo data available for {turn_type}-turn ASR calculation")

print("\nComplete.") 