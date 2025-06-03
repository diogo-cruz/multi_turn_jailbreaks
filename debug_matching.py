import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('../../csv_results/master_results.csv')
model_info = pd.read_csv('../../model_comparison.csv')

print('=== EXPERIMENTAL DATA MODELS ===')
exp_models = sorted(df['target_model'].unique())
print(f'Number of unique models in experimental data: {len(exp_models)}')
for i, model in enumerate(exp_models):
    print(f'{i+1:2d}. {model}')

print('\n=== MODEL COMPARISON DATA ===')
comp_models = sorted(model_info['Model'].unique())
print(f'Number of unique models in comparison data: {len(comp_models)}')
for i, model in enumerate(comp_models):
    print(f'{i+1:2d}. {model}')

print('\n=== MATCHING ANALYSIS ===')
# Simple matching attempt
matched = 0
unmatched_exp = []
matches = []

for exp_model in exp_models:
    found = False
    for comp_model in comp_models:
        if (comp_model.lower() in exp_model.lower() or 
            exp_model.lower() in comp_model.lower() or
            any(part in exp_model.lower() for part in comp_model.lower().split('/')[-1].split('-')[:2])):
            matched += 1
            found = True
            matches.append((exp_model, comp_model))
            break
    if not found:
        unmatched_exp.append(exp_model)

print(f'Matched models: {matched}/{len(exp_models)} ({100*matched/len(exp_models):.1f}%)')

print('\nSuccessful matches:')
for exp, comp in matches:
    print(f'  {exp} -> {comp}')

print(f'\nUnmatched experimental models ({len(unmatched_exp)}):')
for model in unmatched_exp:
    print(f'  - {model}')

# Check reasoning data availability
print('\n=== REASONING DATA ANALYSIS ===')
reasoning_counts = df['reasoning'].value_counts(dropna=False)
print('Reasoning level counts:')
print(reasoning_counts)

# Check temperature data
print('\n=== TEMPERATURE DATA ANALYSIS ===')
temp_counts = df['target_temp'].value_counts()
print('Temperature counts:')
print(temp_counts) 