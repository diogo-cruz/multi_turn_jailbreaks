import pandas as pd
import ast

# This script is purely to test with existing results whether they look sane when processed
# by plot_main_graphs_from_csv.py. This SHOULD NOT be part of our pipeline. ONLY TESTING.

def transform_score(score):
    # Convert string representation of list to actual list if needed
    if isinstance(score, str):
        try:
            score = ast.literal_eval(score)
        except:
            return score
    
    # Handle single scores
    if isinstance(score, (int, float)):
        return round((10 - score) / 9.0, 2)
    
    # Handle lists of scores
    if isinstance(score, list):
        return [transform_score(s) for s in score]
    
    return score

def main():
    # Read the input CSV
    input_file = 'results_strongreject.csv'
    output_file = 'results_strongreject_transformed.csv'
    
    df = pd.read_csv(input_file)
    
    # Transform the scores column
    df['scores'] = df['scores'].apply(transform_score)
    
    # Save to new CSV
    df.to_csv(output_file, index=False)
    print(f"Transformed scores saved to {output_file}")

if __name__ == "__main__":
    main() 