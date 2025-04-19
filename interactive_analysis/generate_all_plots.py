#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def create_figures_dir():
    """Create figures directory if it doesn't exist"""
    figures_dir = os.path.join(os.path.dirname(__file__), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    print(f"Figures directory: {figures_dir}")
    return figures_dir

def run_script(script_name):
    """Run a Python script and measure execution time"""
    print(f"\n{'='*80}")
    print(f"Running {script_name}...")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Run the script as a subprocess
    result = subprocess.run(
        [sys.executable, script_name], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Print output and error (if any)
    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)
    
    elapsed_time = time.time() - start_time
    
    print(f"\nFinished {script_name} in {elapsed_time:.2f} seconds")
    print(f"Return code: {result.returncode}")
    
    return result.returncode == 0

def main():
    """Main function to run all visualization scripts"""
    print("Starting generation of all matplotlib plots...")
    
    # Create figures directory
    figures_dir = create_figures_dir()
    
    # List of scripts to run
    scripts = [
        "generate_plots.py",
        "generate_heatmaps.py",
        "generate_scatter_plots.py"
    ]
    
    # Track success/failure of each script
    results = {}
    
    # Run each script
    for script in scripts:
        script_path = os.path.join(os.path.dirname(__file__), script)
        if os.path.exists(script_path):
            success = run_script(script_path)
            results[script] = "SUCCESS" if success else "FAILED"
        else:
            print(f"Script not found: {script_path}")
            results[script] = "NOT FOUND"
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for script, status in results.items():
        print(f"{script}: {status}")
    
    print("\nAll plots have been generated in the figures directory:")
    print(figures_dir)
    
    # Count number of generated files
    figure_files = os.listdir(figures_dir)
    png_count = sum(1 for f in figure_files if f.endswith('.png'))
    pdf_count = sum(1 for f in figure_files if f.endswith('.pdf'))
    
    print(f"\nGenerated {png_count} PNG files and {pdf_count} PDF files")
    print("="*80)

if __name__ == "__main__":
    main() 