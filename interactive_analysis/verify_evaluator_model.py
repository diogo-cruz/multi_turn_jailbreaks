import pandas as pd

def verify_evaluator_models():
    try:
        # Load the merged file
        df = pd.read_csv('enhanced_master_data.csv')
        
        # Check if required columns exist
        if 'source_file' not in df.columns or 'evaluator_model' not in df.columns:
            print("Required columns missing from the merged file.")
            return
        
        # Get the unique source files and count rows by source and evaluator model
        results = df.groupby(['source_file', 'evaluator_model']).size().reset_index(name='count')
        
        print("Source file and evaluator model verification:")
        print("--------------------------------------------")
        
        # Check each source file to verify it has the correct evaluator model
        for _, row in results.iterrows():
            source = row['source_file']
            evaluator = row['evaluator_model']
            count = row['count']
            
            expected_evaluator = ""
            if source == 'results_2D.csv':
                expected_evaluator = 'anthropic/claude-3-haiku'
            elif source == 'results_2D_2.csv':
                expected_evaluator = 'openai/gpt-4.1-mini'
            else:
                expected_evaluator = 'gpt-4o-mini-2024-07-18'
                
            status = "✓" if evaluator == expected_evaluator else "✗"
            print(f"{status} {source}: {count} rows with evaluator_model = '{evaluator}'")
            if evaluator != expected_evaluator:
                print(f"   Expected: '{expected_evaluator}'")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_evaluator_models() 