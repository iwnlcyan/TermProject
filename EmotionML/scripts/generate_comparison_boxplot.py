"""
Generate Box Plots for 4-Mode Comparison Results (Base vs Retrain vs Full vs Half)
Aligned with generate_boxplot.py style.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid')

def load_results(json_path):
    """Load LOO results from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def extract_data(data):
    """Extract accuracies and times for all 4 modes"""
    accs = {
        'Base': [], 'Retrain': [], 'Full': [], 'Half': []
    }
    times = {
        'Base': [], 'Retrain': [], 'Full': [], 'Half': []
    }
    user_ids = []
    
    for user_id, results in data['users'].items():
        user_ids.append(int(user_id))
        
        # Accuracies
        accs['Base'].append(results['base_accuracy'] * 100)
        accs['Retrain'].append(results['retrain_accuracy'] * 100)
        accs['Full'].append(results['full_accuracy'] * 100)
        accs['Half'].append(results['half_accuracy'] * 100)
        
        # Times - Full/Half use Stage 2 time only (not total)
        times['Base'].append(results['base_time_sec'])
        times['Retrain'].append(results['retrain_time_sec'])
        times['Full'].append(results['full_time_sec'])      # Stage 2 only
        times['Half'].append(results['half_time_sec'])      # Stage 2 only
        
    return user_ids, accs, times

def create_boxplot(data_list, labels, colors, title, ylabel, output_path, y_limit=None):
    """Create box plot with individual points and statistics"""
    
    fig, ax = plt.subplots(figsize=(12, 7))  # Increased height
    
    # Create box plot
    bp = ax.boxplot(data_list, 
                     tick_labels=labels,
                     patch_artist=True,
                     widths=0.6,
                     showfliers=False)
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add individual points (Jitter)
    for i, (data, color) in enumerate(zip(data_list, colors), 1):
        x = np.random.normal(i, 0.04, size=len(data))
        ax.scatter(x, data, alpha=0.6, color=color, edgecolors='black', linewidth=0.5, s=40)
    
    # Calculate and display statistics
    means = [np.mean(d) for d in data_list]
    stds = [np.std(d) for d in data_list]
    
    # Position text BELOW x-axis labels to avoid overlap with title
    # Use annotation with offset for cleaner positioning
    for i, (mean, std) in enumerate(zip(means, stds), 1):
        # Determine unit based on ylabel
        unit = '%' if '%' in ylabel else 's'
        # Place text below the box (at y = min_val - offset)
        y_min_data = min([min(d) for d in data_list])
        
        if y_limit:
            text_y = y_limit[0] + (y_limit[1] - y_limit[0]) * 0.02
        else:
            text_y = y_min_data * 0.85
            
        ax.text(i, text_y, f'{mean:.1f} ± {std:.1f}{unit}', 
                ha='center', va='bottom', fontsize=10, fontweight='bold', 
                color=colors[i-1])
    
    # Labels and title
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)  # Added padding
    
    if y_limit:
        ax.set_ylim(y_limit)
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_path).replace('.png', '.pdf'), bbox_inches='tight')
    print(f"Saved: {output_path}")

def print_statistics(user_ids, accs, times):
    """Print detailed statistics"""
    
    print("\n" + "="*60)
    print("LOO Cross-Validation Comparison Summary")
    print("="*60)
    print(f"Number of users: {len(user_ids)}")
    
    print(f"\n[ACCURACY]")
    print(f"{'Mode':<30} | {'Mean':<15} | {'Min (User)':<20} | {'Max (User)':<20}")
    print("-" * 95)
    
    # Order: Base, Retrain, Full, Half
    order = ['Base', 'Retrain', 'Full', 'Half']
    labels = {
        'Base': 'Base Model Training',
        'Retrain': 'Training from Scratch',
        'Full': 'Full Layer Fine-tuning',
        'Half': 'Partial Layer Fine-tuning'
    }
    
    for mode in order:
        data = accs[mode]
        mean_val = np.mean(data)
        std_val = np.std(data)
        min_val = np.min(data)
        min_user = user_ids[np.argmin(data)]
        max_val = np.max(data)
        max_user = user_ids[np.argmax(data)]
        
        print(f"{labels[mode]:<30} | {mean_val:.1f}% ± {std_val:.1f}% | {min_val:.1f}% (User {min_user}) | {max_val:.1f}% (User {max_user})")
        
    print(f"\n[TRAINING TIME]")
    print(f"{'Mode':<30} | {'Mean':<15} | {'Min (User)':<20} | {'Max (User)':<20}")
    print("-" * 95)
    
    time_labels = {
        'Base': 'Base Model Training',
        'Retrain': 'Training from Scratch',
        'Full': 'Full Layer Fine-tuning (S2)',
        'Half': 'Partial Layer Fine-tuning (S2)'
    }
    
    for mode in order:
        data = times[mode]
        mean_val = np.mean(data)
        std_val = np.std(data)
        min_val = np.min(data)
        min_user = user_ids[np.argmin(data)]
        max_val = np.max(data)
        max_user = user_ids[np.argmax(data)]
        
        print(f"{time_labels[mode]:<30} | {mean_val:.1f}s ± {std_val:.1f}s | {min_val:.1f}s (User {min_user}) | {max_val:.1f}s (User {max_user})")
        
    print("="*60)

if __name__ == "__main__":
    # Paths
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "loo_cv"
    output_dir = script_dir.parent / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find the latest results file
    json_files = list(results_dir.glob("loo_compare_all_*.json"))
    if not json_files:
        print("No comparison results files found!")
        exit(1)
    
    # Use the most recent file (by timestamp in filename)
    latest_file = sorted(json_files)[-1]
    print(f"Loading: {latest_file}")
    
    # Load and process data
    data = load_results(latest_file)
    user_ids, accs, times = extract_data(data)
    
    # Print statistics
    print_statistics(user_ids, accs, times)
    
    # -------------------------------------------------------
    # Common Settings
    # -------------------------------------------------------
    # Academic Labels (matching CHI Poster terminology)
    # ORDER: Base → Full → Partial → Retrain (our method in middle, references on sides)
    labels = [
        'Base Model\nTraining', 
        'Full Layer\nFine-tuning', 
        'Partial Layer\nFine-tuning',
        'Training from\nScratch'
    ]
    
    # Colors: Blue (Base), Orange (Full), Red (Partial), Purple (Retrain)
    colors = ['#3498db', '#e67e22', '#e74c3c', '#9b59b6'] 
    
    # Data Lists: Base → Full → Half → Retrain
    acc_data_list = [accs['Base'], accs['Full'], accs['Half'], accs['Retrain']]
    time_data_list = [times['Base'], times['Full'], times['Half'], times['Retrain']]
    
    # -------------------------------------------------------
    # 1. Individual Accuracy Box Plot (legacy)
    # -------------------------------------------------------
    output_path_acc = output_dir / "results_comparison_boxplot.png"
    create_boxplot(acc_data_list, labels, colors, 
                   f'Accuracy Comparison by Training Mode (LOO CV, N={len(user_ids)})', 
                   'Accuracy (%)', 
                   output_path_acc, 
                   y_limit=(20, 110))
                   
    # -------------------------------------------------------
    # 2. Individual Time Box Plot (legacy)
    # -------------------------------------------------------
    output_path_time = output_dir / "time_comparison_boxplot.png"
    create_boxplot(time_data_list, labels, colors, 
                   f'Training Time Comparison (LOO CV, N={len(user_ids)})', 
                   'Time (seconds)', 
                   output_path_time,
                   y_limit=(0, 220))
    
    # -------------------------------------------------------
    # 3. MERGED Box Plot (Accuracy + Time side by side)
    # -------------------------------------------------------
    np.random.seed(42)  # For reproducible jitter
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Helper function for subplot
    def draw_subplot(ax, data_list, labels, colors, title, ylabel, y_limit=None):
        bp = ax.boxplot(data_list, 
                        tick_labels=labels,
                        patch_artist=True,
                        widths=0.6,
                        showfliers=False)
        
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Add individual points
        for i, (d, color) in enumerate(zip(data_list, colors), 1):
            x = np.random.normal(i, 0.04, size=len(d))
            ax.scatter(x, d, alpha=0.6, color=color, edgecolors='black', linewidth=0.5, s=35)
        
        # Statistics text
        means = [np.mean(d) for d in data_list]
        stds = [np.std(d) for d in data_list]
        unit = '%' if '%' in ylabel else 's'
        
        for i, (mean, std) in enumerate(zip(means, stds), 1):
            text_y = y_limit[0] + (y_limit[1] - y_limit[0]) * 0.02 if y_limit else min([min(d) for d in data_list]) * 0.85
            ax.text(i, text_y, f'{mean:.1f} ± {std:.1f}{unit}', 
                    ha='center', va='bottom', fontsize=13, fontweight='bold', color=colors[i-1])
        
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        if y_limit:
            ax.set_ylim(y_limit)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Left: Accuracy
    draw_subplot(axes[0], acc_data_list, labels, colors, 
                 f'(a) Accuracy (LOO CV, N={len(user_ids)})', 'Accuracy (%)', (20, 110))
    
    # Right: Time
    draw_subplot(axes[1], time_data_list, labels, colors, 
                 f'(b) Training Time (LOO CV, N={len(user_ids)})', 'Time (seconds)', (0, 220))
    
    plt.tight_layout()
    
    output_path_merged = output_dir / "merged_comparison_boxplot.png"
    plt.savefig(output_path_merged, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_path_merged).replace('.png', '.pdf'), bbox_inches='tight')
    print(f"Saved MERGED: {output_path_merged}")
