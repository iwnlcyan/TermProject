"""
Leave-One-Out (LOO) Cross-Validation for EmotionAR Personalization Study
2-Stage Pipeline with Early Stopping and MLflow Tracking

Following EmojiHeroVR paper methodology:
  - EfficientNet-B0 with ImageNet pretrained weights
  - User-based validation split (8 users for validation)
  - 2-Stage Training: Base -> Personalize

Stages:
  Stage 1 (Base): Train on 28 users (8 users for validation, 1 LOO user)
  Stage 2 (Personalize): Fine-tune with Base + Personal data
    - Option A: Full layers trainable (default)
    - Option B: Classifier only (--classifier-only flag)
"""

import os
import sys
import argparse
import json
import random
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from tqdm import tqdm
import torchvision
from mlflow.models.signature import infer_signature

# MLflow
import mlflow
from mlflow import pytorch as mlflow_pytorch

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    # RTX 4090 optimization: enable cuDNN auto-tuner for fastest convolution algorithms
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.enabled = True

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "emoji-hero-vr-db-si"
RESULTS_DIR = PROJECT_DIR / "results" / "loo_cv"

# Emotion labels
EMOTIONS = ['Anger', 'Disgust', 'Fear', 'Happiness', 'Neutral', 'Sadness', 'Surprise']

# Paper-matched augmentations (translation/zoom via affine)
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class EmojiHeroDataset(Dataset):
    """Custom dataset for EmojiHeroVR images."""
    
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform or val_transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]


def get_user_id_from_filename(filename):
    """Extract user ID from filename format: timestamp-0-USER_ID-session-..."""
    parts = os.path.basename(filename).split('-')
    return parts[2]


def collect_all_data():
    """Collect all image paths organized by user and emotion."""
    import glob
    user_data = defaultdict(lambda: {'images': [], 'labels': []})
    
    for emotion_idx, emotion in enumerate(EMOTIONS):
        emotion_dir = DATA_DIR / emotion
        if emotion_dir.exists():
            for img_path in glob.glob(str(emotion_dir / "*.jpg")) + glob.glob(str(emotion_dir / "*.png")):
                user_id = get_user_id_from_filename(img_path)
                user_data[user_id]['images'].append(img_path)
                user_data[user_id]['labels'].append(emotion_idx)
    
    return dict(user_data)


def balance_dataset(images, labels, seed=42):
    """Balance dataset by undersampling to minimum class frequency."""
    from collections import Counter
    
    rng = random.Random(seed)
    class_counts = Counter(labels)
    if not class_counts:
        return [], []
    min_count = min(class_counts.values())
    
    class_samples = {c: [] for c in range(7)}
    for img, lbl in zip(images, labels):
        class_samples[lbl].append(img)
    
    balanced_images, balanced_labels = [], []
    for class_idx in range(7):
        samples = class_samples[class_idx]
        if len(samples) > min_count:
            rng.shuffle(samples)
            samples = samples[:min_count]
        balanced_images.extend(samples)
        balanced_labels.extend([class_idx] * len(samples))
    
    combined = list(zip(balanced_images, balanced_labels))
    rng.shuffle(combined)
    if not combined:
        return [], []
    balanced_images, balanced_labels = zip(*combined)
    
    return list(balanced_images), list(balanced_labels)


def create_loo_splits(user_data, leave_out_user, seed=42, personal_test_ratio=0.2):
    """
    Create train/val/test splits for 2-Stage LOO pipeline.
    
    Split: 28 train / 8 val / 1 LOO user (total 37 users)
    - Stage 1: Train on 28 users, validate on 8 users, test on LOO user (20% holdout)
    - Stage 2: Add LOO user calibration data (80%) to training, test on LOO user (20% holdout)
    
    NOTE: Personal data is split 80/20 to prevent data leakage between train and test.
    """
    all_users = [u for u in user_data.keys() if u != leave_out_user]
    
    rng = random.Random(seed)
    rng.shuffle(all_users)
    
    n_train = 28
    n_val = 8
    
    train_users = set(all_users[:n_train])
    val_users = set(all_users[n_train:n_train + n_val])
    
    train_images, train_labels = [], []
    val_images, val_labels = [], []
    personal_images, personal_labels = [], []
    
    for user_id, data in user_data.items():
        if user_id == leave_out_user:
            personal_images.extend(data['images'])
            personal_labels.extend(data['labels'])
        elif user_id in train_users:
            train_images.extend(data['images'])
            train_labels.extend(data['labels'])
        elif user_id in val_users:
            val_images.extend(data['images'])
            val_labels.extend(data['labels'])
    
    # Split personal data 80/20 for train/test to prevent data leakage
    personal_combined = list(zip(personal_images, personal_labels))
    rng.shuffle(personal_combined)
    
    n_test = max(1, int(len(personal_combined) * personal_test_ratio))
    test_data = personal_combined[:n_test]
    calibration_data = personal_combined[n_test:]
    
    if test_data:
        test_images_split, test_labels_split = zip(*test_data)
        test_images_split, test_labels_split = list(test_images_split), list(test_labels_split)
    else:
        test_images_split, test_labels_split = [], []
    
    if calibration_data:
        calibration_images, calibration_labels = zip(*calibration_data)
        calibration_images, calibration_labels = list(calibration_images), list(calibration_labels)
    else:
        calibration_images, calibration_labels = [], []
    
    # Balance validation set (test set uses all available samples for reliability)
    val_images_balanced, val_labels_balanced = balance_dataset(val_images, val_labels, seed)
    
    print(f"  [Split] Train: {len(train_users)} users ({len(train_images)} images)")
    print(f"  [Split] Val: {len(val_users)} users ({len(val_images_balanced)} images, balanced)")
    print(f"  [Split] Personal (LOO User {leave_out_user}): {len(personal_images)} total images")
    print(f"         └── Calibration (80%): {len(calibration_images)} images (for Stage 2 training)")
    print(f"         └── Test (20%): {len(test_images_split)} images (held out, never seen during training)")
    
    return {
        'train': {'images': train_images, 'labels': train_labels},
        'val': {'images': val_images_balanced, 'labels': val_labels_balanced},
        'test': {'images': test_images_split, 'labels': test_labels_split},
        'personal': {'images': calibration_images, 'labels': calibration_labels},  # Now only calibration portion
        'train_users': len(train_users),
        'val_users': len(val_users),
        'personal_total': len(personal_images),
        'personal_calibration': len(calibration_images),
        'personal_test': len(test_images_split),
    }


def create_model(num_classes=7, pretrained=True):
    """Create EfficientNet-B0 model."""
    model = timm.create_model('efficientnet_b0', pretrained=pretrained)
    model.classifier = nn.Linear(model.classifier.in_features, num_classes)
    return model


def setup_partial_unfreeze(model, unfreeze_ratio='third'):
    """
    Freeze layers based on unfreeze ratio.
    
    EfficientNet-B0 has 7 blocks (blocks.0 to blocks.6):
    - 'third': unfreeze last 1/3 (blocks.5, 6) + classifier
    - 'half': unfreeze last 2/3 (blocks.3, 4, 5, 6) + classifier
    - 'full': unfreeze all layers (no freezing)
    """
    if unfreeze_ratio == 'full':
        for param in model.parameters():
            param.requires_grad = True
        print(f"  [Unfreeze: full] All layers trainable")
        return model
    
    # Define blocks to unfreeze based on ratio
    if unfreeze_ratio == 'third':
        unfreeze_blocks = [5, 6]  # ~1/3 of network
    elif unfreeze_ratio == 'half':
        unfreeze_blocks = [3, 4, 5, 6]  # ~2/3 of network
    else:
        raise ValueError(f"Unknown unfreeze_ratio: {unfreeze_ratio}")
    
    for param in model.parameters():
        param.requires_grad = False
    
    for name, param in model.named_parameters():
        # Classifier always trainable
        if 'classifier' in name:
            param.requires_grad = True
        # Unfreeze specified blocks
        for block_num in unfreeze_blocks:
            if f'blocks.{block_num}' in name:
                param.requires_grad = True
    
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  [Unfreeze: {unfreeze_ratio}] Blocks {unfreeze_blocks} + classifier")
    print(f"  [Unfreeze: {unfreeze_ratio}] Trainable: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")
    
    return model


def calculate_class_weights(labels, device):
    """Calculate inverse class frequencies for weighted loss."""
    from collections import Counter
    counts = Counter(labels)
    total = len(labels)
    num_classes = 7
    
    weights = []
    for i in range(num_classes):
        count = counts[i] if i in counts else 0
        if count > 0:
            weights.append(total / (num_classes * count))
        else:
            weights.append(1.0)
            
    return torch.FloatTensor(weights).to(device)


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


def train_with_early_stopping(model, train_loader, val_loader, optimizer, criterion, 
                               device, epochs, patience=10, stage_name="Training"):
    """Training loop with early stopping, Mixed Precision, and MLflow logging."""
    best_val_acc = 0
    best_model_state = None
    patience_counter = 0
    
    # Mixed Precision for faster training on RTX 4090
    scaler = torch.amp.GradScaler('cuda')
    
    for epoch in range(epochs):
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0
        
        for images, labels in tqdm(train_loader, desc=f"{stage_name} Epoch {epoch+1}", leave=False):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            
            # Mixed Precision forward pass
            with torch.amp.autocast('cuda'):
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            # Scaled backward pass
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        train_acc = train_correct / train_total
        avg_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                with torch.amp.autocast('cuda'):
                    outputs = model(images)
                preds = outputs.argmax(dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        val_acc = accuracy_score(all_labels, all_preds) if all_labels else 0
        val_f1 = f1_score(all_labels, all_preds, average='macro') if all_labels else 0
        
        mlflow.log_metrics({
            f"{stage_name}_train_loss": avg_loss,
            f"{stage_name}_train_acc": train_acc,
            f"{stage_name}_val_acc": val_acc,
            f"{stage_name}_val_f1": val_f1,
        }, step=epoch)
        
        print(f"  Epoch {epoch+1}: Loss={avg_loss:.4f}, Train Acc={train_acc:.4f}, Val Acc={val_acc:.4f}")
        
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


def stage1_base_training(train_data, val_data, device, epochs=50, batch_size=64, lr=1e-4, patience=10):
    """Stage 1: Train base model on 28 users. Returns model and training time."""
    start_time = time.time()
    print("\n[Stage 1] Training Base Model (28 users)...")
    
    train_dataset = EmojiHeroDataset(train_data['images'], train_data['labels'], transform=train_transform)
    val_dataset = EmojiHeroDataset(val_data['images'], val_data['labels'], transform=val_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=8, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=8, pin_memory=True, persistent_workers=True)
    
    model = create_model().to(device)
    
    class_weights = calculate_class_weights(train_data['labels'], device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    for param in model.parameters():
        param.requires_grad = True
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    model, best_val_acc = train_with_early_stopping(
        model, train_loader, val_loader, optimizer, criterion,
        device, epochs=epochs, patience=patience, stage_name="Stage1"
    )
    
    training_time = time.time() - start_time
    mlflow.log_metric("stage1_best_val_acc", best_val_acc)
    mlflow.log_metric("stage1_training_time_sec", training_time)
    print(f"  [Stage 1 Complete] Best Val Acc: {best_val_acc*100:.2f}%, Time: {training_time:.1f}s")
    
    return model, training_time


def stage2_personalize(base_model, train_data, val_data, personal_data, device, 
                       epochs=50, batch_size=64, lr=1e-5, patience=10, 
                       classifier_only=False, unfreeze_ratio='full'):
    """
    Stage 2: Personalize model with Base + Personal data. Returns model and training time.
    
    Args:
        classifier_only: If True, only train classifier layer.
        unfreeze_ratio: 'full', 'half' (2/3), or 'third' (1/3) of layers to unfreeze.
    """
    start_time = time.time()
    
    if classifier_only:
        mode = "Classifier Only"
    elif unfreeze_ratio == 'third':
        mode = "Unfreeze 1/3 (blocks.5, 6)"
    elif unfreeze_ratio == 'half':
        mode = "Unfreeze 2/3 (blocks.3-6)"
    else:
        mode = "Full Layers"
    print(f"\n[Stage 2] Personalization ({mode})...")
    
    # Combine base train data with personal data
    combined_images = train_data['images'] + personal_data['images']
    combined_labels = train_data['labels'] + personal_data['labels']
    
    train_dataset = EmojiHeroDataset(combined_images, combined_labels, transform=train_transform)
    val_dataset = EmojiHeroDataset(val_data['images'], val_data['labels'], transform=val_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=8, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=8, pin_memory=True, persistent_workers=True)
    
    model = base_model.to(device)
    
    if classifier_only:
        # Freeze backbone, train only classifier
        for param in model.parameters():
            param.requires_grad = False
        for param in model.classifier.parameters():
            param.requires_grad = True
        optimizer = optim.Adam(model.classifier.parameters(), lr=lr)
    elif unfreeze_ratio in ['third', 'half']:
        # Train only partial layers based on ratio
        model = setup_partial_unfreeze(model, unfreeze_ratio=unfreeze_ratio)
        trainable_params = [p for p in model.parameters() if p.requires_grad]
        optimizer = optim.Adam(trainable_params, lr=lr)
    else:
        # Train all layers
        for param in model.parameters():
            param.requires_grad = True
        optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Keep class weights for methodological consistency across stages.
    class_weights = calculate_class_weights(combined_labels, device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    model, best_val_acc = train_with_early_stopping(
        model, train_loader, val_loader, optimizer, criterion,
        device, epochs, patience, "Stage2"
    )
    
    training_time = time.time() - start_time
    mlflow.log_metric("stage2_best_val_acc", best_val_acc)
    mlflow.log_metric("stage2_training_time_sec", training_time)
    print(f"  [Stage 2 Complete] Best Val Acc: {best_val_acc*100:.2f}%, Time: {training_time:.1f}s")
    
    return model, training_time


def evaluate_model(model, test_data, device, batch_size=32, stage_name="test"):
    """Evaluate model on test data."""
    if len(test_data['images']) == 0:
        return {'accuracy': 0, 'f1': 0, 'n_samples': 0, 'confusion_matrix': []}
    
    dataset = EmojiHeroDataset(test_data['images'], test_data['labels'], transform=val_transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    model.eval()
    all_preds, all_labels = [], []
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')
    cm = confusion_matrix(all_labels, all_preds)
    
    mlflow.log_metric(f"{stage_name}_test_accuracy", acc)
    mlflow.log_metric(f"{stage_name}_test_f1", f1)
    
    return {'accuracy': acc, 'f1': f1, 'n_samples': len(all_labels), 'confusion_matrix': cm.tolist()}


def run_loo_cv(args):
    """Run Leave-One-Out Cross-Validation with 2-stage pipeline."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    if args.retrain:
        mode_str = "Retrain from Scratch"
    elif args.classifier_only:
        mode_str = "Classifier Only"
    else:
        mode_str = f"Unfreeze: {args.unfreeze_ratio}"
    print(f"Mode: {mode_str}")
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.retrain:
        mode_suffix = "retrain"
    elif args.classifier_only:
        mode_suffix = "classifier"
    else:
        mode_suffix = args.unfreeze_ratio  # 'full', 'half', or 'third'
    results_file = RESULTS_DIR / f"loo_2stage_{mode_suffix}_{timestamp}.json"
    
    mlruns_dir = PROJECT_DIR / "mlruns"
    mlflow.set_tracking_uri(f"file:///{mlruns_dir.as_posix()}")
    mlflow.set_experiment("loo_cv_2stage")
    
    print("Collecting data...")
    user_data = collect_all_data()
    all_users = sorted(user_data.keys(), key=int)
    print(f"Found {len(all_users)} users")
    
    results = {'timestamp': timestamp, 'mode': mode_suffix, 'users': {}, 'summary': {}}
    
    for leave_out_user in all_users:
        if args.user and str(leave_out_user) != str(args.user):
            continue
        
        print(f"\n{'='*60}")
        print(f"LOO: Leaving out User {leave_out_user}")
        print(f"{'='*60}")
        
        splits = create_loo_splits(user_data, leave_out_user)
        personal_data = splits['personal']
        val_loader_for_signature = DataLoader(
            EmojiHeroDataset(splits['val']['images'], splits['val']['labels'], transform=val_transform),
            batch_size=64, shuffle=False, num_workers=0
        )
        input_example = get_input_example(val_loader_for_signature, device)
        pip_requirements = get_pip_requirements()
        
        with mlflow.start_run(run_name=f"LOO_User_{leave_out_user}_{mode_suffix}"):
            mlflow.log_params({
                "leave_out_user": leave_out_user,
                "mode": mode_suffix,
                "train_users": splits['train_users'],
                "val_users": splits['val_users'],
                "train_images": len(splits['train']['images']),
                "personal_images": len(personal_data['images']),
                "epochs": args.epochs,
                "patience": args.patience,
                "classifier_only": args.classifier_only,
                "unfreeze_ratio": args.unfreeze_ratio,
                "retrain": args.retrain,
            })
            
            # RETRAIN MODE: Train from scratch with combined data
            if args.retrain:
                print(f"\n[RETRAIN MODE] Training from ImageNet weights with combined data...")
                
                # Combine train data with personal calibration data (same as Stage 2)
                combined_images = splits['train']['images'] + personal_data['images']
                combined_labels = splits['train']['labels'] + personal_data['labels']
                
                print(f"  Train data: {len(splits['train']['images'])} (base) + {len(personal_data['images'])} (personal) = {len(combined_images)} total")
                
                train_dataset = EmojiHeroDataset(combined_images, combined_labels, transform=train_transform)
                val_dataset = EmojiHeroDataset(splits['val']['images'], splits['val']['labels'], transform=val_transform)
                
                train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=8, pin_memory=True, persistent_workers=True)
                val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=8, pin_memory=True, persistent_workers=True)
                
                # Create fresh model from ImageNet weights
                start_time = time.time()
                model = create_model(pretrained=True).to(device)
                
                class_weights = calculate_class_weights(combined_labels, device)
                criterion = nn.CrossEntropyLoss(weight=class_weights)
                
                for param in model.parameters():
                    param.requires_grad = True
                optimizer = optim.Adam(model.parameters(), lr=1e-4)
                
                model, best_val_acc = train_with_early_stopping(
                    model, train_loader, val_loader, optimizer, criterion,
                    device, epochs=args.epochs, patience=args.patience, stage_name="Retrain"
                )
                
                retrain_time = time.time() - start_time
                retrain_results = evaluate_model(model, splits['test'], device, stage_name="retrain")
                
                print(f"[RETRAIN] Test Acc: {retrain_results['accuracy']*100:.2f}%, Training Time: {retrain_time:.1f}s")
                
                mlflow.log_metrics({
                    "retrain_training_time_sec": retrain_time,
                    "retrain_test_accuracy": retrain_results['accuracy'],
                    "retrain_best_val_acc": best_val_acc,
                })
                
                # Log model
                retrain_input_example, retrain_signature = build_signature(model, input_example)
                mlflow_pytorch.log_model(
                    model,
                    name="model_retrain",
                    input_example=retrain_input_example,
                    signature=retrain_signature,
                    pip_requirements=pip_requirements,
                )
                
                # Store results (use retrain as both stage1 and stage2 for consistency)
                stage1_results = retrain_results
                stage2_results = retrain_results
                stage1_time = retrain_time
                stage2_time = 0
                improvement = 0  # No improvement since single training
                
            else:
                # STANDARD 2-STAGE PIPELINE
                # Stage 1: Train base model
                base_model, stage1_time = stage1_base_training(
                    splits['train'], splits['val'], device,
                    epochs=args.epochs, patience=args.patience
                )
                stage1_results = evaluate_model(base_model, splits['test'], device, stage_name="stage1")
                print(f"[Stage 1] Test Acc: {stage1_results['accuracy']*100:.2f}%, Training Time: {stage1_time:.1f}s")
                
                # Log Stage 1 model to MLflow
                stage1_input_example, stage1_signature = build_signature(base_model, input_example)
                mlflow_pytorch.log_model(
                    base_model,
                    name="model_stage1",
                    input_example=stage1_input_example,
                    signature=stage1_signature,
                    pip_requirements=pip_requirements,
                )
                
                # Skip Stage 2 if --stage1-only flag is set
                if args.stage1_only:
                    print(f"\n[Stage 1 Only Mode] Skipping Stage 2 (Personalization)")
                    stage2_results = {'accuracy': 0, 'f1': 0, 'n_samples': 0}
                    stage2_time = 0
                    improvement = 0
                    mlflow.log_metrics({
                        "final_stage1_acc": stage1_results['accuracy'],
                        "stage1_only": 1,
                        "total_training_time_sec": stage1_time,
                    })
                else:
                    # Stage 2: Personalize
                    personalized_model, stage2_time = stage2_personalize(
                        base_model, splits['train'], splits['val'], personal_data, device,
                        epochs=args.epochs, patience=args.patience, 
                        classifier_only=args.classifier_only, unfreeze_ratio=args.unfreeze_ratio
                    )
                    stage2_results = evaluate_model(personalized_model, splits['test'], device, stage_name="stage2")
                    print(f"[Stage 2] Test Acc: {stage2_results['accuracy']*100:.2f}%, Training Time: {stage2_time:.1f}s")
                    stage2_input_example, stage2_signature = build_signature(personalized_model, input_example)
                    mlflow_pytorch.log_model(
                        personalized_model,
                        name="model_stage2",
                        input_example=stage2_input_example,
                        signature=stage2_signature,
                        pip_requirements=pip_requirements,
                    )
                    
                    # Summary
                    total_time = stage1_time + stage2_time
                    improvement = stage2_results['accuracy'] - stage1_results['accuracy']
                    print(f"\nUser {leave_out_user} Results:")
                    print(f"   Stage 1 (Base):        {stage1_results['accuracy']*100:.2f}% (Time: {stage1_time:.1f}s)")
                    print(f"   Stage 2 (Personalize): {stage2_results['accuracy']*100:.2f}% ({improvement*100:+.2f}%p, Time: {stage2_time:.1f}s)")
                    print(f"   Total Training Time:   {total_time:.1f}s")
                    
                    mlflow.log_metrics({
                        "final_stage1_acc": stage1_results['accuracy'],
                        "final_stage2_acc": stage2_results['accuracy'],
                        "improvement": improvement,
                        "total_training_time_sec": total_time,
                    })
        
        results['users'][leave_out_user] = {
            'stage1_accuracy': stage1_results['accuracy'],
            'stage1_f1': stage1_results['f1'],
            'stage2_accuracy': stage2_results['accuracy'],
            'stage2_f1': stage2_results['f1'],
            'improvement': improvement,
            'n_samples': stage1_results['n_samples'],
            'stage1_time_sec': stage1_time,
            'stage2_time_sec': stage2_time,
            'total_time_sec': stage1_time + stage2_time,
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    # Summary statistics
    if results['users']:
        s1_accs = [r['stage1_accuracy'] for r in results['users'].values()]
        s2_accs = [r['stage2_accuracy'] for r in results['users'].values()]
        improvements = [r['improvement'] for r in results['users'].values()]
        s1_times = [r['stage1_time_sec'] for r in results['users'].values()]
        s2_times = [r['stage2_time_sec'] for r in results['users'].values()]
        total_times = [r['total_time_sec'] for r in results['users'].values()]
        
        import numpy as np
        results['summary'] = {
            'n_users': len(results['users']),
            'mode': mode_suffix,
            'mean_stage1_acc': float(np.mean(s1_accs)),
            'std_stage1_acc': float(np.std(s1_accs)),
            'mean_stage2_acc': float(np.mean(s2_accs)),
            'std_stage2_acc': float(np.std(s2_accs)),
            'mean_improvement': float(np.mean(improvements)),
            'std_improvement': float(np.std(improvements)),
            'mean_stage1_time_sec': float(np.mean(s1_times)),
            'mean_stage2_time_sec': float(np.mean(s2_times)),
            'mean_total_time_sec': float(np.mean(total_times)),
        }
        
        print(f"\n{'='*60}")
        print(f"FINAL SUMMARY ({mode_suffix.upper()} MODE)")
        print(f"{'='*60}")
        print(f"Mean Stage 1 (Base):        {results['summary']['mean_stage1_acc']*100:.2f}% ± {results['summary']['std_stage1_acc']*100:.2f}%")
        print(f"Mean Stage 2 (Personalize): {results['summary']['mean_stage2_acc']*100:.2f}% ± {results['summary']['std_stage2_acc']*100:.2f}%")
        print(f"Mean Improvement:           {results['summary']['mean_improvement']*100:+.2f}%p ± {results['summary']['std_improvement']*100:.2f}%p")
        print(f"Mean Training Time:         {results['summary']['mean_total_time_sec']:.1f}s (S1: {results['summary']['mean_stage1_time_sec']:.1f}s, S2: {results['summary']['mean_stage2_time_sec']:.1f}s)")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")


def run_compare_modes(args):
    """
    Compare ALL 4 methods using the SAME data splits for fair comparison:
    1. Base (Stage 1 only)
    2. Retrain (from ImageNet with combined data)
    3. Full Fine-tuning (all layers)
    4. Half Fine-tuning (blocks.3-6 only)
    
    Full and Half Fine-tuning share the SAME Stage 1 base model.
    """
    import copy
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    print("=" * 60)
    print("COMPARE ALL MODES: Base vs Retrain vs Full vs Half")
    print("=" * 60)
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"loo_compare_all_{timestamp}.json"
    
    mlruns_dir = PROJECT_DIR / "mlruns"
    mlflow.set_tracking_uri(f"file:///{mlruns_dir.as_posix()}")
    mlflow.set_experiment("loo_cv_compare_all")
    
    print("Collecting data...")
    user_data = collect_all_data()
    all_users = sorted(user_data.keys(), key=int)
    print(f"Found {len(all_users)} users")
    
    results = {
        'timestamp': timestamp, 
        'mode': 'compare_all', 
        'users': {}, 
        'summary': {}
    }
    
    for leave_out_user in all_users:
        if args.user and str(leave_out_user) != str(args.user):
            continue
        
        print(f"\n{'='*60}")
        print(f"LOO: Leaving out User {leave_out_user}")
        print(f"{'='*60}")
        
        splits = create_loo_splits(user_data, leave_out_user)
        personal_data = splits['personal']
        
        with mlflow.start_run(run_name=f"LOO_User_{leave_out_user}_compare_all"):
            mlflow.log_params({
                "leave_out_user": leave_out_user,
                "mode": "compare_all",
                "train_users": splits['train_users'],
                "val_users": splits['val_users'],
                "train_images": len(splits['train']['images']),
                "personal_images": len(personal_data['images']),
                "epochs": args.epochs,
                "patience": args.patience,
            })
            
            # =============================================
            # 1. Stage 1: Train BASE model (shared for Full/Half)
            # =============================================
            print("\n--- [1/4] Training BASE Model (Stage 1) ---")
            base_model, stage1_time = stage1_base_training(
                splits['train'], splits['val'], device,
                epochs=args.epochs, patience=args.patience
            )
            base_results = evaluate_model(base_model, splits['test'], device, stage_name="base")
            print(f"[BASE] Test Acc: {base_results['accuracy']*100:.2f}%, Training Time: {stage1_time:.1f}s")
            
            # Save base model state for Full/Half comparison
            base_model_state = copy.deepcopy(base_model.state_dict())
            
            # =============================================
            # 2. RETRAIN: Train from ImageNet with combined data
            # =============================================
            print("\n--- [2/4] Training RETRAIN Model (from ImageNet) ---")
            combined_images = splits['train']['images'] + personal_data['images']
            combined_labels = splits['train']['labels'] + personal_data['labels']
            
            retrain_dataset = EmojiHeroDataset(combined_images, combined_labels, transform=train_transform)
            val_dataset = EmojiHeroDataset(splits['val']['images'], splits['val']['labels'], transform=val_transform)
            
            retrain_loader = DataLoader(retrain_dataset, batch_size=64, shuffle=True, num_workers=8, pin_memory=True, persistent_workers=True)
            val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=8, pin_memory=True, persistent_workers=True)
            
            retrain_start = time.time()
            retrain_model = create_model(pretrained=True).to(device)
            
            class_weights = calculate_class_weights(combined_labels, device)
            criterion = nn.CrossEntropyLoss(weight=class_weights)
            
            for param in retrain_model.parameters():
                param.requires_grad = True
            optimizer = optim.Adam(retrain_model.parameters(), lr=1e-4)
            
            retrain_model, _ = train_with_early_stopping(
                retrain_model, retrain_loader, val_loader, optimizer, criterion,
                device, epochs=args.epochs, patience=args.patience, stage_name="Retrain"
            )
            retrain_time = time.time() - retrain_start
            retrain_results = evaluate_model(retrain_model, splits['test'], device, stage_name="retrain")
            print(f"[RETRAIN] Test Acc: {retrain_results['accuracy']*100:.2f}%, Training Time: {retrain_time:.1f}s")
            
            # =============================================
            # 3. FULL Fine-tuning (from Base model)
            # =============================================
            print("\n--- [3/4] Training FULL Fine-tuning ---")
            model_full = create_model().to(device)
            model_full.load_state_dict(base_model_state)
            
            personalized_full, full_time = stage2_personalize(
                model_full, splits['train'], splits['val'], personal_data, device,
                epochs=args.epochs, patience=args.patience, 
                classifier_only=False, unfreeze_ratio='full'
            )
            full_results = evaluate_model(personalized_full, splits['test'], device, stage_name="full")
            print(f"[FULL] Test Acc: {full_results['accuracy']*100:.2f}%, Training Time: {full_time:.1f}s")
            
            # =============================================
            # 4. HALF Fine-tuning (from SAME Base model)
            # =============================================
            print("\n--- [4/4] Training HALF Fine-tuning ---")
            model_half = create_model().to(device)
            model_half.load_state_dict(base_model_state)
            
            personalized_half, half_time = stage2_personalize(
                model_half, splits['train'], splits['val'], personal_data, device,
                epochs=args.epochs, patience=args.patience, 
                classifier_only=False, unfreeze_ratio='half'
            )
            half_results = evaluate_model(personalized_half, splits['test'], device, stage_name="half")
            print(f"[HALF] Test Acc: {half_results['accuracy']*100:.2f}%, Training Time: {half_time:.1f}s")
            
            # =============================================
            # Summary for this user
            # =============================================
            print(f"\n{'='*50}")
            print(f"User {leave_out_user} Comparison Results:")
            print(f"{'='*50}")
            print(f"  [BASE]    {base_results['accuracy']*100:.2f}% (Time: {stage1_time:.1f}s)")
            print(f"  [RETRAIN] {retrain_results['accuracy']*100:.2f}% (Time: {retrain_time:.1f}s)")
            print(f"  [FULL]    {full_results['accuracy']*100:.2f}% (Time: {stage1_time + full_time:.1f}s total)")
            print(f"  [HALF]    {half_results['accuracy']*100:.2f}% (Time: {stage1_time + half_time:.1f}s total)")
            print(f"{'='*50}")
            
            mlflow.log_metrics({
                "base_acc": base_results['accuracy'],
                "retrain_acc": retrain_results['accuracy'],
                "full_acc": full_results['accuracy'],
                "half_acc": half_results['accuracy'],
                "base_time": stage1_time,
                "retrain_time": retrain_time,
                "full_total_time": stage1_time + full_time,
                "half_total_time": stage1_time + half_time,
            })
        
        results['users'][leave_out_user] = {
            'base_accuracy': base_results['accuracy'],
            'retrain_accuracy': retrain_results['accuracy'],
            'full_accuracy': full_results['accuracy'],
            'half_accuracy': half_results['accuracy'],
            'n_samples': base_results['n_samples'],
            'base_time_sec': stage1_time,
            'retrain_time_sec': retrain_time,
            'full_time_sec': full_time,
            'half_time_sec': half_time,
            'full_total_time_sec': stage1_time + full_time,
            'half_total_time_sec': stage1_time + half_time,
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    # Summary statistics
    if results['users']:
        base_accs = [r['base_accuracy'] for r in results['users'].values()]
        retrain_accs = [r['retrain_accuracy'] for r in results['users'].values()]
        full_accs = [r['full_accuracy'] for r in results['users'].values()]
        half_accs = [r['half_accuracy'] for r in results['users'].values()]
        retrain_times = [r['retrain_time_sec'] for r in results['users'].values()]
        full_total_times = [r['full_total_time_sec'] for r in results['users'].values()]
        half_total_times = [r['half_total_time_sec'] for r in results['users'].values()]
        
        results['summary'] = {
            'n_users': len(results['users']),
            'mean_base_acc': float(np.mean(base_accs)),
            'std_base_acc': float(np.std(base_accs)),
            'mean_retrain_acc': float(np.mean(retrain_accs)),
            'std_retrain_acc': float(np.std(retrain_accs)),
            'mean_full_acc': float(np.mean(full_accs)),
            'std_full_acc': float(np.std(full_accs)),
            'mean_half_acc': float(np.mean(half_accs)),
            'std_half_acc': float(np.std(half_accs)),
            'mean_retrain_time': float(np.mean(retrain_times)),
            'mean_full_total_time': float(np.mean(full_total_times)),
            'mean_half_total_time': float(np.mean(half_total_times)),
        }
        
        print(f"\n{'='*60}")
        print("FINAL SUMMARY: All Methods Comparison")
        print(f"{'='*60}")
        print(f"  [BASE]    {results['summary']['mean_base_acc']*100:.2f}% ± {results['summary']['std_base_acc']*100:.2f}%")
        print(f"  [RETRAIN] {results['summary']['mean_retrain_acc']*100:.2f}% ± {results['summary']['std_retrain_acc']*100:.2f}% (Time: {results['summary']['mean_retrain_time']:.1f}s)")
        print(f"  [FULL]    {results['summary']['mean_full_acc']*100:.2f}% ± {results['summary']['std_full_acc']*100:.2f}% (Time: {results['summary']['mean_full_total_time']:.1f}s)")
        print(f"  [HALF]    {results['summary']['mean_half_acc']*100:.2f}% ± {results['summary']['std_half_acc']*100:.2f}% (Time: {results['summary']['mean_half_total_time']:.1f}s)")
        print(f"{'='*60}")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(description="LOO CV with 2-Stage Pipeline")
    parser.add_argument('--user', type=str, help="Run LOO for specific user only")
    parser.add_argument('--epochs', type=int, default=50, help="Epochs per stage")
    parser.add_argument('--patience', type=int, default=10, help="Early stopping patience")
    parser.add_argument('--classifier-only', action='store_true', 
                        help="Stage 2: Train classifier only (default: all layers)")
    parser.add_argument('--unfreeze-ratio', type=str, default='full', choices=['full', 'half', 'third'],
                        help="Stage 2 unfreeze ratio: 'full' (all layers), 'half' (2/3 = blocks.3-6), 'third' (1/3 = blocks.5-6)")
    parser.add_argument('--stage1-only', action='store_true',
                        help="Run only Stage 1 (Base model) for timing measurement")
    parser.add_argument('--retrain', action='store_true',
                        help="Retrain from scratch with combined data (28 users + LOO calibration) for comparison")
    parser.add_argument('--compare-modes', action='store_true',
                        help="Compare Full vs Half fine-tuning using the SAME Stage 1 base model for fair comparison")
    
    args = parser.parse_args()
    
    if args.compare_modes:
        run_compare_modes(args)
    else:
        run_loo_cv(args)


if __name__ == "__main__":
    main()
