"""
Generate Sample Analysis Charts: Base Model vs Partial Layer Fine-tuning
Shows relationship between sample size and accuracy improvement
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap

# Set style
plt.style.use('seaborn-v0_8-whitegrid')

# Colors matching generate_comparison_boxplot.py
COLORS = {
    'Base': '#3498db',      # Blue
    'Half': '#e74c3c'       # Red
}

def load_results(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def extract_data(data):
    """Extract data from loo_compare_all JSON format
    
    Note: n_samples in JSON is the TEST sample count (20% of user's data).
    We calculate training samples as n_samples * 4 (since 80/20 split).
    """
    users = []
    test_samples = []   # Original n_samples (20% for testing)
    train_samples = []  # Calibration samples (80% for training)
    base_accs = []
    half_accs = []
    improvements = []
    
    for user_id, results in data['users'].items():
        users.append(int(user_id))
        test_n = results['n_samples']
        test_samples.append(test_n)
        # Training samples = test_samples * 4 (80/20 split means train = 4x test)
        train_samples.append(test_n * 4)
        base_accs.append(results['base_accuracy'] * 100)
        half_accs.append(results['half_accuracy'] * 100)
        improvements.append((results['half_accuracy'] - results['base_accuracy']) * 100)
    
    return users, train_samples, base_accs, half_accs, improvements

def create_sample_analysis(users, n_samples, base_accs, half_accs, improvements, output_path):
    """Create sample analysis charts comparing Base vs Partial Fine-tuning"""
    
    # Calculate mean for threshold
    mean_samples = np.mean(n_samples)
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # -------------------------------------------------------
    # Subplot 1: Slope Chart (Base → Partial Fine-tuning)
    # -------------------------------------------------------
    ax1 = axes[0]
    
    # Separate users into 3 categories
    improved_idx = [i for i, imp in enumerate(improvements) if imp > 0]
    no_change_idx = [i for i, imp in enumerate(improvements) if imp == 0]
    decreased_idx = [i for i, imp in enumerate(improvements) if imp < 0]
    
    # X positions: 0 = Base, 1 = Personalized
    np.random.seed(42)
    x_jitter = np.random.uniform(-0.05, 0.05, len(users))
    x_base = 0 + x_jitter
    x_pers = 1 + x_jitter
    y_jitter = np.random.uniform(-1.5, 1.5, len(users))
    
    # Draw slope lines for each user
    # Green for improved
    for i in improved_idx:
        ax1.plot([x_base[i], x_pers[i]], [base_accs[i] + y_jitter[i], half_accs[i] + y_jitter[i]], 
                 '-', color='#2ecc71', alpha=0.5, linewidth=1.5, zorder=2)
    # Yellow for no change
    for i in no_change_idx:
        ax1.plot([x_base[i], x_pers[i]], [base_accs[i] + y_jitter[i], half_accs[i] + y_jitter[i]], 
                 '-', color='#f1c40f', alpha=0.5, linewidth=1.5, zorder=1)
    # Gray for decreased
    for i in decreased_idx:
        ax1.plot([x_base[i], x_pers[i]], [base_accs[i] + y_jitter[i], half_accs[i] + y_jitter[i]], 
                 '-', color='#95a5a6', alpha=0.5, linewidth=1.5, zorder=1)
    
    # Custom Red-to-Blue colormap based on sample size
    cmap_colors = ["#e74c3c", "#3498db"]  # Red to Blue
    cmap = LinearSegmentedColormap.from_list("RedBlue", cmap_colors)
    norm = plt.Normalize(vmin=min(n_samples), vmax=max(n_samples))
    
    # Plot no change users (yellow)
    for i in no_change_idx:
        ax1.scatter([x_base[i]], [base_accs[i] + y_jitter[i]], 
                    c='#f1c40f', s=40, alpha=0.7, edgecolors='#d4a500', linewidth=0.5, zorder=1)
        ax1.scatter([x_pers[i]], [half_accs[i] + y_jitter[i]], 
                    c='#f1c40f', s=40, alpha=0.7, edgecolors='#d4a500', linewidth=0.5, zorder=1)
    
    # Plot decreased users (gray)
    for i in decreased_idx:
        ax1.scatter([x_base[i]], [base_accs[i] + y_jitter[i]], 
                    c='#95a5a6', s=40, alpha=0.7, edgecolors='#7f8c8d', linewidth=0.5, zorder=1)
        ax1.scatter([x_pers[i]], [half_accs[i] + y_jitter[i]], 
                    c='#95a5a6', s=40, alpha=0.7, edgecolors='#7f8c8d', linewidth=0.5, zorder=1)
    
    # Plot improved users with color based on sample size
    random_zorder = np.random.randint(3, 40, len(improved_idx))
    
    for idx, i in enumerate(improved_idx):
        color = cmap(norm(n_samples[i]))
        z = random_zorder[idx]
        ax1.scatter([x_base[i]], [base_accs[i] + y_jitter[i]], 
                    c=[color], s=55, edgecolors='black', linewidth=0.5, zorder=z, alpha=1.0)
        ax1.scatter([x_pers[i]], [half_accs[i] + y_jitter[i]], 
                    c=[color], s=55, edgecolors='black', linewidth=0.5, zorder=z, alpha=1.0)
    
    # Add Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax1, fraction=0.046, pad=0.04)
    cbar.set_label('Training Samples', fontsize=10)
    
    # Add labels for users with smallest sample sizes (bottom 3)
    sorted_by_samples = sorted(range(len(n_samples)), key=lambda i: n_samples[i])
    labeled_indices = set()
    for rank, i in enumerate(sorted_by_samples[:3]):
        labeled_indices.add(i)
        ax1.annotate(f'U{users[i]} (N={n_samples[i]})', 
                     xy=(x_base[i], base_accs[i] + y_jitter[i]),
                     xytext=(x_base[i] - 0.2, base_accs[i] + y_jitter[i]),
                     fontsize=8, ha='right', va='center',
                     arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))
    
    # Add label for user with lowest base model accuracy
    lowest_base_idx = np.argmin(base_accs)
    if lowest_base_idx not in labeled_indices:
        ax1.annotate(f'U{users[lowest_base_idx]} (N={n_samples[lowest_base_idx]})', 
                     xy=(x_base[lowest_base_idx], base_accs[lowest_base_idx] + y_jitter[lowest_base_idx]),
                     xytext=(x_base[lowest_base_idx] - 0.2, base_accs[lowest_base_idx] + y_jitter[lowest_base_idx]),
                     fontsize=8, ha='right', va='center',
                     arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))
    
    # Formatting
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['Base Model\nTraining', 'Partial Layer\nFine-tuning'], fontsize=11)
    ax1.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Personalization Effect by Sample Size', fontsize=13, fontweight='bold')
    ax1.set_xlim(-0.5, 1.5)
    ax1.set_ylim(20, 105)
    ax1.grid(True, axis='y', alpha=0.3)
    
    # Custom legend for lines
    custom_lines = [Line2D([0], [0], color='#2ecc71', lw=2),
                    Line2D([0], [0], color='#f1c40f', lw=2),
                    Line2D([0], [0], color='#95a5a6', lw=2)]
    ax1.legend(custom_lines, ['Improved', 'No Change', 'Decreased'], loc='lower right', fontsize=9)
    
    # -------------------------------------------------------
    # Subplot 2: Sample Size Distribution (Bar)
    # -------------------------------------------------------
    ax2 = axes[1]
    
    # Sort by n_samples
    sorted_data = sorted(zip(users, n_samples, half_accs, improvements), key=lambda x: x[1])
    sorted_users, sorted_samples, sorted_accs, sorted_imps = zip(*sorted_data)
    
    # Color: yellow for no change, gray for decreased, red/blue for improved (based on mean)
    colors = []
    for s, imp in zip(sorted_samples, sorted_imps):
        if imp == 0:
            colors.append('#f1c40f')  # Yellow for no change
        elif imp < 0:
            colors.append('#95a5a6')  # Gray for decreased
        elif s < mean_samples:
            colors.append('#e74c3c')  # Red for below mean (improved)
        else:
            colors.append('#3498db')  # Blue for above mean (improved)
    
    bars = ax2.bar(range(len(sorted_users)), sorted_samples, color=colors, edgecolor='black', alpha=0.7)
    
    ax2.set_xlabel('User ID', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Training Samples', fontsize=12, fontweight='bold')
    ax2.set_title('Training Sample Size per User', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(sorted_users)))
    ax2.set_xticklabels([f'U{u}' for u in sorted_users], rotation=45, fontsize=8)
    ax2.axhline(y=mean_samples, color='green', linestyle='--', label=f'Mean ({mean_samples:.1f})')
    
    # Legend
    legend_elements = [
        Patch(facecolor='#e74c3c', edgecolor='black', alpha=0.7, label='Below mean (improved)'),
        Patch(facecolor='#3498db', edgecolor='black', alpha=0.7, label='Above mean (improved)'),
        Patch(facecolor='#f1c40f', edgecolor='black', alpha=0.7, label='No change'),
        Patch(facecolor='#95a5a6', edgecolor='black', alpha=0.7, label='Decreased'),
        Line2D([0], [0], color='green', linestyle='--', label=f'Mean ({mean_samples:.1f})')
    ]
    ax2.legend(handles=legend_elements, loc='upper left', fontsize=8)
    ax2.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_path).replace('.png', '.pdf'), bbox_inches='tight')
    print(f"Saved: {output_path}")
    
    # Print statistics
    print(f"\n{'='*60}")
    print("Sample Size Statistics")
    print(f"{'='*60}")
    print(f"Min samples: {min(n_samples)} (User {users[n_samples.index(min(n_samples))]})")
    print(f"Max samples: {max(n_samples)} (User {users[n_samples.index(max(n_samples))]})")
    print(f"Mean samples: {mean_samples:.1f}")
    print(f"Users improved: {len(improved_idx)}/{len(users)}")
    print(f"Users no change: {len(no_change_idx)}/{len(users)}")
    print(f"Users decreased: {len(decreased_idx)}/{len(users)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "loo_cv"
    output_dir = script_dir.parent / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find latest compare_all file
    json_files = list(results_dir.glob("loo_compare_all_*.json"))
    if not json_files:
        print("No comparison results files found!")
        exit(1)
    
    latest_file = sorted(json_files)[-1]
    print(f"Loading: {latest_file}")
    
    data = load_results(latest_file)
    users, n_samples, base_accs, half_accs, improvements = extract_data(data)
    
    output_path = output_dir / "sample_analysis.png"
    create_sample_analysis(users, n_samples, base_accs, half_accs, improvements, output_path)
