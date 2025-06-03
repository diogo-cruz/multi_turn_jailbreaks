#!/usr/bin/env python3
"""
Generate all plots for the paper.
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """Run a plotting script and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running {script_name}...")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(f"✓ {script_name} completed successfully")
        if result.stdout:
            print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {script_name}:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error running {script_name}: {e}")
        return False
    
    return True

def main():
    """Generate all plots"""
    print("Starting plot generation for paper...")
    
    # Automatically find all plotting scripts in current directory
    current_dir = Path('.')
    scripts = []
    
    # Find all Python files that start with 'plot_' to avoid running this script itself
    for script_path in current_dir.glob('plot_*.py'):
        if script_path.is_file():
            scripts.append(script_path.name)
    
    # Sort for consistent ordering
    scripts = sorted(scripts)
    
    if not scripts:
        print("No plotting scripts found (looking for plot_*.py files)")
        return
    
    print(f"Found {len(scripts)} plotting scripts:")
    for script in scripts:
        print(f"  - {script}")
    
    # Track results
    results = {}
    
    # Run each script
    for script in scripts:
        results[script] = run_script(script)
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    success_count = sum(results.values())
    total_count = len(scripts)
    
    for script, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{script:30} {status}")
    
    print(f"\nCompleted: {success_count}/{total_count} plots generated successfully")
    
    if success_count == total_count:
        print("\n🎉 All plots generated successfully!")
        print(f"Plots saved to: {Path('../plots').resolve()}")
    else:
        print(f"\n⚠️  {total_count - success_count} plots failed to generate")
        print("Check the error messages above for details")
        sys.exit(1)

if __name__ == '__main__':
    main() 