#!/usr/bin/env python3
"""
Generate all plots for the paper based on the new requirements.
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """Run a plotting script and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print(f"{'='*60}")
    
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
    print("=" * 60)
    print("This script generates plots based on the new requirements:")
    print("- Single-turn vs Multi-turn comparison (Cleveland dot plot)")
    print("- ASR vs number of refusals analysis")
    print("- Qualitative analysis with PCA/UMAP")
    print("- Heatmaps of test cases vs tactics")
    print("=" * 60)
    
    # List of scripts to run in order
    scripts = [
        'plot_single_vs_multi_turn.py',
        'plot_asr_vs_refusals.py',
        'plot_qualitative_analysis.py',
        'plot_heatmap_tactics_testcases.py'
    ]
    
    # Verify all scripts exist
    missing_scripts = []
    for script in scripts:
        if not Path(script).exists():
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Missing scripts: {missing_scripts}")
        return False
    
    print(f"Found all {len(scripts)} plotting scripts")
    
    # Track results
    results = {}
    
    # Run each script
    for script in scripts:
        results[script] = run_script(script)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(results.values())
    total_count = len(scripts)
    
    for script, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{script:<35} {status}")
    
    print(f"\nCompleted: {success_count}/{total_count} plots generated successfully")
    
    if success_count == total_count:
        print("\n🎉 All plots generated successfully!")
        plots_dir = Path('../plots').resolve()
        print(f"Plots saved to: {plots_dir}")
        
        # List generated plots
        if plots_dir.exists():
            plot_files = list(plots_dir.glob('*.pdf'))
            print(f"\nGenerated {len(plot_files)} PDF plots:")
            for plot_file in sorted(plot_files):
                print(f"  - {plot_file.name}")
        
        print("\nPlot descriptions:")
        print("- single_vs_multi_turn_cleveland.pdf: Cleveland dot plot comparing single vs multi-turn ASR")
        print("- single_vs_multi_turn_bars.pdf: Bar chart alternative for single vs multi-turn comparison")
        print("- asr_vs_refusals_main.pdf: ASR vs number of refusals allowed (both approaches)")
        print("- asr_vs_refusals_by_tactic.pdf: ASR vs refusals broken down by tactic")
        print("- qualitative_pca_tactics.pdf: PCA analysis of tactics and test cases")
        print("- qualitative_pca_models.pdf: PCA analysis focused on models")
        print("- qualitative_umap_*.pdf: UMAP versions (if available)")
        print("- heatmap_testcases_tactics_aggregated.pdf: Heatmap of test cases vs tactics")
        print("- heatmap_testcases_tactics_by_model.pdf: Model-specific heatmaps")
        
    else:
        print(f"\n⚠️  {total_count - success_count} plots failed to generate")
        print("Check the error messages above for details")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 