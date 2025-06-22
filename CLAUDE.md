# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a framework for testing and evaluating LLM vulnerabilities through automated multi-turn jailbreak attacks. The project automates jailbreak attacks by using one AI (attacker model) to compromise another (target model), focusing on multi-turn conversations rather than traditional single-prompt attacks.

## Key Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies (includes ruff linter)
pip install -r requirements-dev.txt

# Install meta-evaluation dependencies
pip install -r requirements_meta_evaluation.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OPENROUTER_API_KEY, GEMINI_API_KEY)
```

### Running Attacks

#### Single Attack
```bash
python main.py --jailbreak-tactic "crescendomation" --test-case "counterfeit_money" --target-model "gpt-4" --attacker-model "gpt-4o"
```

#### Parallel Attacks
```bash
# Make scripts executable
chmod +x run_attacks_parallel.sh
chmod +x run_attacks_parallel_batch_*.sh

# Run parallel attacks
./run_attacks_parallel.sh
```

### Analysis and Evaluation

#### Generate Plots
```bash
# Basic plotting
python plot_results.py --turn-type multi --temp 0.0 --plot-type model

# Plot specific results
python plot_scripts/plot_main_graphs_from_csv.py
python paper_plots/src/generate_all_plots.py
```

#### Meta-Evaluation Analysis
```bash
# Test meta-evaluation setup
python test_meta_evaluation.py

# Run meta-evaluation analysis
python meta_evaluation_analysis.py
python run_sample_meta_evaluation.py
python run_human_overlap_meta_evaluation.py
```

#### Human Evaluation Interface
```bash
cd human-evaluator
npm install
npm run dev
# Access at http://localhost:3000
```

### Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .
```

### Data Analysis
```bash
# Create master CSV from results
python create_master_csv.py

# Compare human vs AI evaluations
python compare_human_ai_evaluations.py

# Analyze disagreements
python analyze_human_ai_disagreements.py
python detailed_disagreement_analysis.py
```

## Architecture Overview

### Core Components

- **`main.py`**: Main entry point for running attacks
- **`utils/`**: Core utilities for model interaction and evaluation
  - `generate.py`: Standardized model generation interface
  - `run.py`: Core execution engine for jailbreak attacks
  - `evaluate_with_strongreject.py`: Evaluation using StrongREJECT methodology
  - `reasoning_utils.py`: Utilities for handling reasoning-capable models
- **`jailbreaks/`**: Modular jailbreak tactic implementations
  - Each tactic has `prompt_single_turn.py` and `prompt_multi_turn.py`
  - Tactics: crescendomation, actor_attack, command, crowding, emotional_appeal, etc.
- **`test_cases/`**: JSON files defining harm scenarios (30 from StrongREJECT)
- **`clean_results/`**: Processed experiment results in JSONL format

### Analysis Components

- **`plot_scripts/`**: Visualization tools for attack effectiveness
- **`paper_plots/`**: Publication-ready plot generation
- **`meta_evaluation_analysis.py`**: Identifies evaluation issues (false positives, capability problems)
- **`human-evaluator/`**: Next.js app for manual response evaluation
- **`reasoning_analysis/`**: Tools for analyzing reasoning model behavior

### Data Flow

1. **Attack Execution**: `main.py` → `utils/run.py` → jailbreak tactic → target model
2. **Evaluation**: StrongREJECT scoring system evaluates responses (0.0-1.0 scale)
3. **Analysis**: Multiple analysis scripts process results for insights
4. **Visualization**: Plot generation for research and presentation

### Model Support

- **Target Models**: Various LLMs via OpenRouter API (GPT, Claude, Gemini, Llama, etc.)
- **Attacker Models**: Models that generate jailbreak prompts
- **Reasoning Models**: Special handling for models with internal reasoning (o1, DeepSeek-R1, QwQ)

### Result Storage Structure
```
./clean_results/final_runs/{batch}/
├── {tactic}/
│   └── {tactic}_{testcase}_{model}_{turn_type}_sample{n}_{timestamp}.jsonl
```

## Development Notes

- Jailbreak tactics are modular - new tactics can be added by creating files in `jailbreaks/`
- The framework uses OpenAI API format for model interactions
- Results are stored in JSONL format with conversation history and evaluation scores
- Meta-evaluation helps identify false positives and evaluation issues
- Human evaluation interface provides ground truth for automated evaluation validation

## Research Documentation

### LOGBOOK.md
Use `LOGBOOK.md` to track major research milestones, experimental findings, and significant changes to the codebase. This file should be updated whenever:
- Running major experiments or analysis
- Making significant changes to the framework
- Discovering important research insights
- Implementing new features or methodologies
- Identifying issues with evaluation or meta-evaluation systems

The logbook provides a research timeline separate from git commits, focusing on scientific insights rather than technical implementation details.