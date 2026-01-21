"""
External User Validation for EmotionAR Personalization Study
2-Stage Pipeline: Base (29 train + 8 val users) -> Personalize (External User)

Stages:
  Stage 1 (Base): Train on 29 EmojiHeroVR users (8 users for validation)
  Stage 2 (Personalize): Fine-tune with Base + External user data
    - Option A: Full layers trainable (default)
    - Option B: Classifier only (--classifier-only flag)
"""

import os
import random
import argparse
import json
from datetime import datetime
import glob
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from collections import Counter, defaultdict
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
import timm
import mlflow
import mlflow.pytorch
import torchvision
from mlflow.models.signature import infer_signature

# Paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR_ORIGINAL = PROJECT_DIR / "data/emoji-hero-vr-db-si"
DATA_DIR_EXTERNAL = PROJECT_DIR / "data/occluded"
MLRUNS_DIR = PROJECT_DIR / "mlruns"
RESULTS_DIR = PROJECT_DIR / "results/external_validation"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Device config
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Hyperparameters
IMG_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 0  # Windows Fix
SEED = 42

# Set global seeds for reproducibility
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# Transforms (paper-matched augmentations; translation/zoom via affine)
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Emotion Mapping
EMOTIONS = ['Anger', 'Disgust', 'Fear', 'Happiness', 'Neutral', 'Sadness', 'Surprise']
EMOTION_TO_IDX = {e: i for i, e in enumerate(EMOTIONS)}


class EmojiHeroDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            return torch.zeros((3, IMG_SIZE, IMG_SIZE)), label


def get_user_id_from_filename(filename):
    """Extracts user ID from filename (format: timestamp-0-USER_ID-...)."""
    basename = os.path.basename(filename)
    parts = basename.split('-')
    if len(parts) > 2:
        return parts[2]
    return basename.split('_')[0]


def collect_all_data(data_dir):
    """Collects all data from the given directory (Original DB)."""
    user_data = defaultdict(lambda: {'images': [], 'labels': []})
    for emotion_dir in data_dir.iterdir():
        if emotion_dir.is_dir() and emotion_dir.name in EMOTION_TO_IDX:
            emotion_label = EMOTION_TO_IDX[emotion_dir.name]
            for img_path in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                user_id = get_user_id_from_filename(str(img_path))
                user_data[user_id]['images'].append(str(img_path))
                user_data[user_id]['labels'].append(emotion_label)
    print(f"Collected data for {len(user_data)} users from {data_dir.name}")
    return user_data


def collect_external_data(data_dir, user_id="external"):
    """Collects external data as a single user."""
    external_data = {'images': [], 'labels': []}
    for emotion_dir in data_dir.iterdir():
        if emotion_dir.is_dir() and emotion_dir.name in EMOTION_TO_IDX:
            emotion_label = EMOTION_TO_IDX[emotion_dir.name]
            for img_path in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                external_data['images'].append(str(img_path))
                external_data['labels'].append(emotion_label)
    print(f"Collected {len(external_data['images'])} images for External User {user_id}")
    return {user_id: external_data}


def balance_dataset(images, labels, seed=42):
    """Balances dataset by undersampling."""
    rng = random.Random(seed)
    class_counts = Counter(labels)
    if not class_counts:
        return [], []
    min_count = min(class_counts.values())
    
    balanced_images, balanced_labels = [], []
    class_map = defaultdict(list)
    for img, lbl in zip(images, labels):
        class_map[lbl].append(img)
        
    for i in range(len(EMOTIONS)):
        cls_imgs = class_map[i]
        rng.shuffle(cls_imgs)
        selected = cls_imgs[:min_count]
        balanced_images.extend(selected)
        balanced_labels.extend([i] * len(selected))
        
    combined = list(zip(balanced_images, balanced_labels))
    rng.shuffle(combined)
    if not combined:
        return [], []
    b_imgs, b_lbls = zip(*combined)
    return list(b_imgs), list(b_lbls)


def calculate_class_weights(labels, device):
    weights = compute_class_weight(class_weight='balanced', classes=np.unique(labels), y=labels)
    return torch.tensor(weights, dtype=torch.float32).to(device)

def get_pip_requirements():
    return [
        f"torch=={torch.__version__}",
        f"torchvision=={torchvision.__version__}",
        f"timm=={timm.__version__}",
        f"numpy=={np.__version__}",
    ]


def get_input_example(val_loader, device):
    for images, _ in val_loader:
        return images[:1].to(device)
    return None


def build_signature(model, input_example):
    if input_example is None:
        return None, None
    model.eval()
    with torch.no_grad():
        output = model(input_example)
    input_example_np = input_example.cpu().numpy()
    output_np = output.cpu().numpy()
    signature = infer_signature(input_example_np, output_np)
    return input_example_np, signature


def create_splits(original_data, external_data, seed=42):
    """
    Creates splits for 2-stage pipeline:
    - Stage 1 Train: 29 Original Users (Validation: 8 Original)
    - Stage 2 Train: 30 Users (29 + External User)
    - Test: External User (balanced)
    """
    all_original_users = list(original_data.keys())
    rng = random.Random(seed)
    rng.shuffle(all_original_users)
    
    n_val = 8
    val_users = set(all_original_users[:n_val])
    train_users_original = set(all_original_users[n_val:])  # 29 Users
    
    # Stage 1 Data (29 users)
    s1_images, s1_labels = [], []
    val_images, val_labels = [], []
    
    for user_id, data in original_data.items():
        if user_id in train_users_original:
            s1_images.extend(data['images'])
            s1_labels.extend(data['labels'])
        elif user_id in val_users:
            val_images.extend(data['images'])
            val_labels.extend(data['labels'])
            
    # External User Data
    ext_user_id = list(external_data.keys())[0]
    ext_images = external_data[ext_user_id]['images']
    ext_labels = external_data[ext_user_id]['labels']
    
    # Stage 2 Data (Stage 1 + External)
    s2_images = s1_images + ext_images
    s2_labels = s1_labels + ext_labels
    
    # Balance Validation and Test
    val_images_balanced, val_labels_balanced = balance_dataset(val_images, val_labels, seed)
    test_images_balanced, test_labels_balanced = balance_dataset(ext_images, ext_labels, seed)
    
    print(f"Split Summary:")
    print(f"  Stage 1 Train: {len(train_users_original)} Original Users -> {len(s1_images)} images")
    print(f"  Stage 2 Train: {len(train_users_original) + 1} Users -> {len(s2_images)} images")
    print(f"  Val: {n_val} Original Users -> {len(val_images_balanced)} images (Balanced)")
    print(f"  Test: External User -> {len(test_images_balanced)} images (Balanced)")
    
    return {
        'stage1_train': {'images': s1_images, 'labels': s1_labels},
        'stage2_train': {'images': s2_images, 'labels': s2_labels},
        'val': {'images': val_images_balanced, 'labels': val_labels_balanced},
        'test': {'images': test_images_balanced, 'labels': test_labels_balanced},
        'personal': {'images': ext_images, 'labels': ext_labels},
        'ext_id': ext_user_id
    }


def train_with_early_stopping(model, train_loader, val_loader, optimizer, criterion, device, epochs, patience, stage_name):
    best_val_acc = 0.0
    patience_counter = 0
    best_model_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0
        
        for images, labels in tqdm(train_loader, desc=f"{stage_name} Epoch {epoch+1}", leave=False):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            
        train_acc = train_correct / train_total
        avg_loss = train_loss / len(train_loader)
        
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        val_acc = val_correct / val_total
        
        print(f"  Epoch {epoch+1}: Loss={avg_loss:.4f}, Train Acc={train_acc:.4f}, Val Acc={val_acc:.4f}")
        mlflow.log_metrics({
            f"{stage_name}_train_loss": avg_loss,
            f"{stage_name}_train_acc": train_acc,
            f"{stage_name}_val_acc": val_acc
        }, step=epoch)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  [Early Stopping] at epoch {epoch+1}")
                break
                
    if best_model_state:
        model.load_state_dict(best_model_state)
    return model, best_val_acc


def evaluate_model(model, test_data, device):
    if len(test_data['images']) == 0:
        return {"accuracy": 0.0, "f1": 0.0, "n_samples": 0}
    test_loader = DataLoader(EmojiHeroDataset(test_data['images'], test_data['labels'], transform=val_transform), 
                             batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')
    return {"accuracy": acc, "f1": f1, "n_samples": len(all_labels)}


def main():
    parser = argparse.ArgumentParser(description="External User Validation (2-Stage Pipeline)")
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--patience', type=int, default=10)
    parser.add_argument('--classifier-only', action='store_true',
                        help="Stage 2: Train classifier only (default: all layers)")
    args = parser.parse_args()
    
    mode_suffix = "classifier" if args.classifier_only else "full"
    print(f"Mode: {'Classifier Only' if args.classifier_only else 'Full Layers'}")
    
    mlflow.set_tracking_uri(f"file:///{MLRUNS_DIR.as_posix()}")
    mlflow.set_experiment("external_user_2stage")
    
    print("Collecting Data...")
    original_data = collect_all_data(DATA_DIR_ORIGINAL)
    external_data = collect_external_data(DATA_DIR_EXTERNAL, user_id="external")
    
    splits = create_splits(original_data, external_data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"external_2stage_{mode_suffix}_{timestamp}.json"
    
    with mlflow.start_run(run_name=f"External_User_{mode_suffix}"):
        mlflow.log_params({
            "type": "2-Stage Pipeline",
            "mode": mode_suffix,
            "stage1_users": 29,
            "stage2_users": 30,
            "val_users": 8,
            "target": "External User",
            "epochs": args.epochs,
            "classifier_only": args.classifier_only
        })
        
        # --- Stage 1: Base (29 Users) ---
        print("\n[Stage 1] Base Training (29 Original Users)...")
        train_loader = DataLoader(
            EmojiHeroDataset(splits['stage1_train']['images'], splits['stage1_train']['labels'], transform=train_transform),
            batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
        val_loader = DataLoader(
            EmojiHeroDataset(splits['val']['images'], splits['val']['labels'], transform=val_transform),
            batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
        pip_requirements = get_pip_requirements()
        input_example = get_input_example(val_loader, device)
                                
        model = timm.create_model('efficientnet_b0', pretrained=True, num_classes=7).to(device)
        class_weights = calculate_class_weights(splits['stage1_train']['labels'], device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        optimizer = optim.Adam(model.parameters(), lr=1e-4)
        
        model, _ = train_with_early_stopping(model, train_loader, val_loader, optimizer, criterion, device, args.epochs, args.patience, "Stage1")
        stage1_input_example, stage1_signature = build_signature(model, input_example)
        mlflow.pytorch.log_model(
            model,
            name="model_stage1",
            input_example=stage1_input_example,
            signature=stage1_signature,
            pip_requirements=pip_requirements,
        )
        
        s1_metrics = evaluate_model(model, splits['test'], device)
        print(f"[Stage 1] Test Acc: {s1_metrics['accuracy']*100:.2f}%")
        mlflow.log_metrics({
            "stage1_acc": s1_metrics["accuracy"],
            "stage1_f1": s1_metrics["f1"],
        })
        
        # --- Stage 2: Personalize ---
        print(f"\n[Stage 2] Personalization ({mode_suffix})...")
        train_loader = DataLoader(
            EmojiHeroDataset(splits['stage2_train']['images'], splits['stage2_train']['labels'], transform=train_transform),
            batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
        
        if args.classifier_only:
            # Freeze backbone, train only classifier
            for param in model.parameters():
                param.requires_grad = False
            for param in model.classifier.parameters():
                param.requires_grad = True
            optimizer = optim.Adam(model.classifier.parameters(), lr=1e-5)
        else:
            # All layers trainable
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.Adam(model.parameters(), lr=1e-5)
        
        # Keep class weights for methodological consistency across stages.
        class_weights = calculate_class_weights(splits['stage2_train']['labels'], device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        model, _ = train_with_early_stopping(model, train_loader, val_loader, optimizer, criterion, device, args.epochs, args.patience, "Stage2")
        stage2_input_example, stage2_signature = build_signature(model, input_example)
        mlflow.pytorch.log_model(
            model,
            name="model_stage2",
            input_example=stage2_input_example,
            signature=stage2_signature,
            pip_requirements=pip_requirements,
        )
        
        s2_metrics = evaluate_model(model, splits['test'], device)
        print(f"[Stage 2] Test Acc: {s2_metrics['accuracy']*100:.2f}%")
        mlflow.log_metrics({
            "stage2_acc": s2_metrics["accuracy"],
            "stage2_f1": s2_metrics["f1"],
        })
        
        # Results
        improvement = s2_metrics['accuracy'] - s1_metrics['accuracy']
        print(f"\nFinal Results (External User, {mode_suffix}):")
        print(f"Stage 1 (Base, 29 Users): {s1_metrics['accuracy']*100:.2f}%")
        print(f"Stage 2 (Personalized):   {s2_metrics['accuracy']*100:.2f}% ({improvement*100:+.2f}%p)")
        
        results = {
            "timestamp": timestamp,
            "mode": mode_suffix,
            "target_user": "external",
            "splits": {
                "stage1_users": 29,
                "stage2_users": 30,
                "val_users": 8,
                "stage1_train_images": len(splits['stage1_train']['images']),
                "stage2_train_images": len(splits['stage2_train']['images']),
                "val_images": len(splits['val']['images']),
                "test_images": len(splits['test']['images']),
            },
            "metrics": {
                "stage1": s1_metrics,
                "stage2": s2_metrics,
                "improvement": improvement,
            },
        }
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
