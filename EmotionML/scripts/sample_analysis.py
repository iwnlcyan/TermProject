"""
Generate Scatter Plot: Sample Size vs Accuracy
Shows relationship between number of test samples and model performance
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_results(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def create_sample_analysis(data, output_path):
    """Create scatter plot showing sample size vs accuracy"""
    
    users = []
    n_samples = []
    stage1_accs = []
    stage2_accs = []
    improvements = []
    
    for user_id, results in data['users'].items():
        users.append(int(user_id))
        n_samples.append(results['n_samples'])
        stage1_accs.append(results['stage1_accuracy'] * 100)
        stage2_accs.append(results['stage2_accuracy'] * 100)
        improvements.append(results['improvement'] * 100)
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Subplot 1: Sample Size vs Accuracy
    ax1 = axes[0]
    ax1.scatter(n_samples, stage1_accs, label='Base Model', alpha=0.7, s=80, c='#3498db', edgecolors='black')
    ax1.scatter(n_samples, stage2_accs, label='Personalized', alpha=0.7, s=80, c='#e74c3c', edgecolors='black')
    
    # Connect pairs with lines
    for i in range(len(users)):
        ax1.plot([n_samples[i], n_samples[i]], [stage1_accs[i], stage2_accs[i]], 
                 'g-', alpha=0.3, linewidth=1)
    
    # Highlight User 22
    user22_idx = users.index(22) if 22 in users else None
    if user22_idx is not None:
        ax1.annotate('User 22\n(n=12)', 
                     xy=(n_samples[user22_idx], stage1_accs[user22_idx]),
                     xytext=(n_samples[user22_idx]+10, stage1_accs[user22_idx]+10),
                     fontsize=9, 
                     arrowprops=dict(arrowstyle='->', color='gray'))
    
    ax1.set_xlabel('Number of Test Samples', fontsize=12)
    ax1.set_ylabel('Accuracy (%)', fontsize=12)
    ax1.set_title('Sample Size vs Accuracy', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 105)
    
    # Subplot 2: Sample Size Distribution (Bar)
    ax2 = axes[1]
    
    # Sort by n_samples
    sorted_data = sorted(zip(users, n_samples, stage2_accs), key=lambda x: x[1])
    sorted_users, sorted_samples, sorted_accs = zip(*sorted_data)
    
    colors = ['#e74c3c' if s < 20 else '#3498db' for s in sorted_samples]
    bars = ax2.bar(range(len(sorted_users)), sorted_samples, color=colors, edgecolor='black', alpha=0.7)
    
    ax2.set_xlabel('User ID', fontsize=12)
    ax2.set_ylabel('Number of Test Samples', fontsize=12)
    ax2.set_title('Test Sample Size per User', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(sorted_users)))
    ax2.set_xticklabels([f'U{u}' for u in sorted_users], rotation=45, fontsize=8)
    ax2.axhline(y=28, color='green', linestyle='--', label='Balanced (28 samples)')
    ax2.legend()
    ax2.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    
    # Print statistics
    print(f"\n{'='*50}")
    print("Sample Size Statistics")
    print(f"{'='*50}")
    print(f"Min samples: {min(n_samples)} (User {users[n_samples.index(min(n_samples))]})")
    print(f"Max samples: {max(n_samples)} (User {users[n_samples.index(max(n_samples))]})")
    print(f"Mean samples: {np.mean(n_samples):.1f}")
    print(f"Users with < 28 samples: {sum(1 for s in n_samples if s < 28)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "loo_cv"
    
    # Find latest file
    json_files = list(results_dir.glob("loo_2stage_full_*.json"))
    latest_file = sorted(json_files)[-1]
    print(f"Loading: {latest_file}")
    
    data = load_results(latest_file)
    
    output_path = str(script_dir.parent.parent / "EmotionAR_Poster" / "sample_analysis.png")
    create_sample_analysis(data, output_path)
