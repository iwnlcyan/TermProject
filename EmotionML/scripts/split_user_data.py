import argparse
import shutil
from pathlib import Path
import random

EMOTIONS = ["Anger", "Disgust", "Fear", "Happiness", "Neutral", "Sadness", "Surprise"]

def split_user_data(user_dir: Path, train_ratio: float = 0.8, seed: int = 42):
    random.seed(seed)
    src = Path(user_dir)
    dst_train = src / "training_set"
    dst_val = src / "validation_set"

    dst_train.mkdir(exist_ok=True)
    dst_val.mkdir(exist_ok=True)

    for emotion in EMOTIONS:
        emotion_dir = src / emotion
        if not emotion_dir.exists():
            continue

        files = sorted([f for f in emotion_dir.iterdir() if f.is_file()])
        random.shuffle(files)
        split_idx = int(len(files) * train_ratio)

        train_files = files[:split_idx]
        val_files = files[split_idx:]

        (dst_train / emotion).mkdir(parents=True, exist_ok=True)
        (dst_val / emotion).mkdir(parents=True, exist_ok=True)

        for f in train_files:
            shutil.copy2(f, dst_train / emotion / f.name)
        for f in val_files:
            shutil.copy2(f, dst_val / emotion / f.name)

        print(f"{emotion}: {len(train_files)} train / {len(val_files)} val")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_dir", required=True,
                        help="example: /Users/.../EmotionML/data/personal/user_01")
    parser.add_argument("--train_ratio", type=float, default=0.8,
                        help="train ratio (default 0.8)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    split_user_data(Path(args.user_dir), args.train_ratio, args.seed)