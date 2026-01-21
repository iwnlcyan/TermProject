"""
Generate Box Plot for LOO Cross-Validation Results
Compares Base Model vs Personalized Model accuracy across users
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_results(json_path):
    """Load LOO results from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def extract_accuracies(data):
    """Extract Stage 1 and Stage 2 accuracies from all users"""
    stage1_accs = []
    stage2_accs = []
    user_ids = []
    
    for user_id, results in data['users'].items():
        stage1_accs.append(results['stage1_accuracy'] * 100)
        stage2_accs.append(results['stage2_accuracy'] * 100)
        user_ids.append(int(user_id))
    
    return user_ids, stage1_accs, stage2_accs

def create_boxplot(stage1_accs, stage2_accs, output_path):
    """Create side-by-side box plot comparing Stage 1 vs Stage 2"""
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Prepare data for seaborn
    data = {
        'Stage': ['Base Model'] * len(stage1_accs) + ['Personalized'] * len(stage2_accs),
        'Accuracy (%)': stage1_accs + stage2_accs
    }
    
    # Create box plot
    colors = ['#3498db', '#e74c3c']  # Blue for Base, Red for Personalized
    bp = ax.boxplot([stage1_accs, stage2_accs], 
                     labels=['Base Model', 'Personalized'],
                     patch_artist=True,
                     widths=0.6)
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add individual points
    for i, (accs, color) in enumerate([(stage1_accs, colors[0]), (stage2_accs, colors[1])], 1):
        x = np.random.normal(i, 0.04, size=len(accs))
        ax.scatter(x, accs, alpha=0.6, color=color, edgecolors='black', linewidth=0.5, s=50)
    
    # Calculate and display statistics
    mean1, std1 = np.mean(stage1_accs), np.std(stage1_accs)
    mean2, std2 = np.mean(stage2_accs), np.std(stage2_accs)
    improvement = mean2 - mean1
    
    # Add text annotations
    ax.text(1, max(stage1_accs) + 3, f'{mean1:.1f}% ± {std1:.1f}%', 
            ha='center', fontsize=11, fontweight='bold')
    ax.text(2, max(stage2_accs) + 3, f'{mean2:.1f}% ± {std2:.1f}%', 
            ha='center', fontsize=11, fontweight='bold')
    
    # Add improvement arrow
    ax.annotate('', xy=(1.8, mean2), xytext=(1.2, mean1),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax.text(1.5, (mean1 + mean2) / 2, f'+{improvement:.1f}%p', 
            ha='center', va='bottom', fontsize=12, fontweight='bold', color='green')
    
    # Labels and title
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title(f'Personalization Effect on FER Accuracy\n(Leave-One-Out CV, N={len(stage1_accs)} users)', 
                 fontsize=14, fontweight='bold')
    ax.set_ylim(0, 110)
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.replace('.png', '.pdf'), bbox_inches='tight')
    print(f"Saved: {output_path}")
    
    return mean1, std1, mean2, std2, improvement

def print_statistics(user_ids, stage1_accs, stage2_accs):
    """Print detailed statistics"""
    improvements = [s2 - s1 for s1, s2 in zip(stage1_accs, stage2_accs)]
    
    print("\n" + "="*60)
    print("LOO Cross-Validation Results Summary")
    print("="*60)
    print(f"Number of users: {len(user_ids)}")
    print(f"\nStage 1 (Base Model):")
    print(f"  Mean: {np.mean(stage1_accs):.2f}% ± {np.std(stage1_accs):.2f}%")
    print(f"  Min:  {np.min(stage1_accs):.2f}% (User {user_ids[np.argmin(stage1_accs)]})")
    print(f"  Max:  {np.max(stage1_accs):.2f}% (User {user_ids[np.argmax(stage1_accs)]})")
    print(f"\nStage 2 (Personalized):")
    print(f"  Mean: {np.mean(stage2_accs):.2f}% ± {np.std(stage2_accs):.2f}%")
    print(f"  Min:  {np.min(stage2_accs):.2f}% (User {user_ids[np.argmin(stage2_accs)]})")
    print(f"  Max:  {np.max(stage2_accs):.2f}% (User {user_ids[np.argmax(stage2_accs)]})")
    print(f"\nImprovement:")
    print(f"  Mean: +{np.mean(improvements):.2f}%p")
    print(f"  Min:  +{np.min(improvements):.2f}%p (User {user_ids[np.argmin(improvements)]})")
    print(f"  Max:  +{np.max(improvements):.2f}%p (User {user_ids[np.argmax(improvements)]})")
    print(f"  Users improved: {sum(1 for i in improvements if i > 0)}/{len(improvements)}")
    print("="*60)


if __name__ == "__main__":
    # Paths
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "loo_cv"
    
    # Find the latest results file
    json_files = list(results_dir.glob("loo_2stage_full_*.json"))
    if not json_files:
        print("No results files found!")
        exit(1)
    
    # Use the most recent file (by timestamp in filename)
    latest_file = sorted(json_files)[-1]
    print(f"Loading: {latest_file}")
    
    # Load and process data
    data = load_results(latest_file)
    user_ids, stage1_accs, stage2_accs = extract_accuracies(data)
    
    # Print statistics
    print_statistics(user_ids, stage1_accs, stage2_accs)
    
    # Create box plot
    output_path = str(script_dir.parent.parent / "EmotionAR_Poster" / "results_boxplot.png")
    create_boxplot(stage1_accs, stage2_accs, output_path)
