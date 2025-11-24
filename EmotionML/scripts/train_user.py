"""Utility script to run Stage 1 and Stage 2 training for a given user.

This script is optional, but it helps automate the steps:
1. Run Stage 1 fine-tuning (base dataset + personal dataset).
2. Run Stage 2 fine-tuning (personal dataset only, using registered Stage 1 model).

It assumes you execute it from the repository root, e.g.:

    python EmotionML/scripts/train_user.py --user-id user_01
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Allow "from src import ..." relative to EmotionML package.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
REPO_ROOT = PROJECT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src import train_stage1, train_stage2
from scripts.split_user_data import split_user_data


def _user_suffix(user_id: str) -> str:
    cleaned = user_id.strip()
    lowered = cleaned.lower()
    if lowered.startswith("user_"):
        return cleaned.split("_", 1)[1]
    if lowered.startswith("user-"):
        return cleaned.split("-", 1)[1]
    return cleaned


def _default_export_dir(*parts: str) -> str:
    return str((PROJECT_DIR / "exports" / Path(*parts)).resolve())


def _default_tracking_uri() -> str:
    """Return an sqlite URI pointing to the repo's mlflow.db."""
    mlflow_db = PROJECT_DIR.parent / "mlflow.db"
    return f"sqlite:///{mlflow_db.resolve().as_posix()}"


def _resolve_path(value: str | None, default: Path) -> Path:
    return Path(value).expanduser().resolve() if value else default.resolve()


def build_stage1_params(args: argparse.Namespace, personal_root: Path) -> dict:
    base_root = _resolve_path(
        args.base_root,
        PROJECT_DIR / "data" / "emoji-hero-vr-db-si",
    )
    export_dir = args.stage1_export_dir or _default_export_dir(
        "stage1", args.stage1_model_stage.lower()
    )
    return {
        "base_root": str(base_root),
        "personal_root": str(personal_root),
        "batch_size": args.batch_size,
        "lr": args.stage1_lr,
        "epochs": args.stage1_epochs,
        "num_workers": args.num_workers,
        "tracking_uri": args.tracking_uri,
        "user_id": args.user_id,
        "experiment_name": args.stage1_experiment_name,
        "model_name": args.stage1_model_name,
        "model_stage": args.stage1_model_stage,
        "local_export_dir": export_dir,
    }


def build_stage2_params(args: argparse.Namespace, personal_root: Path) -> dict:
    export_dir = args.stage2_export_dir or _default_export_dir(
        "users", args.user_label, args.stage2_model_stage.lower()
    )
    return {
        "personal_root": str(personal_root),
        "batch_size": args.batch_size,
        "lr": args.stage2_lr,
        "epochs": args.stage2_epochs,
        "num_workers": args.num_workers,
        "user_id": args.user_id,
        "tracking_uri": args.tracking_uri,
        "experiment_name": args.stage2_experiment_name,
        "model_name": args.stage2_model_name,
        "model_stage": args.stage2_model_stage,
        "stage1_model_stage": args.stage1_model_stage,
        "stage1_model_name": args.stage1_model_name,
        "local_export_dir": export_dir,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stage1 + Stage2 training for a user.")
    parser.add_argument("--user-id", required=True, help="User folder name under data/personal/")
    parser.add_argument("--base-root", help="Override base dataset path.")
    parser.add_argument("--personal-root", help="Override personal dataset path.")
    parser.add_argument(
        "--tracking-uri",
        default=_default_tracking_uri(),
        help="MLflow tracking URI (default: %(default)s)",
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Mini-batch size.")
    parser.add_argument("--num-workers", type=int, default=8, help="DataLoader workers.")
    parser.add_argument("--stage1-epochs", type=int, default=50)
    parser.add_argument("--stage2-epochs", type=int, default=50)
    parser.add_argument("--stage1-lr", type=float, default=1e-4)
    parser.add_argument("--stage2-lr", type=float, default=1e-4)
    parser.add_argument(
        "--split-user-data",
        action="store_true",
        help="Run split_user_data.py before training (creates training/validation subsets).",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train ratio when splitting raw personal data.",
    )
    parser.add_argument(
        "--split-seed",
        type=int,
        default=42,
        help="Random seed for split_user_data.",
    )
    parser.add_argument("--skip-stage1", action="store_true", help="Only run Stage2.")
    parser.add_argument("--stage1-experiment-name", default=None)
    parser.add_argument("--stage2-experiment-name", default=None)
    parser.add_argument("--stage1-model-name", default="EmotionAR_Stage1")
    parser.add_argument(
        "--stage2-model-name",
        default=None,
        help="MLflow model name for Stage2. Defaults to 'EmotionAR_User_<user_id suffix>'.",
    )
    parser.add_argument("--stage1-model-stage", default="Production")
    parser.add_argument("--stage2-model-stage", default="Production")
    parser.add_argument(
        "--stage1-export-dir",
        help="Optional override for Stage1 export directory.",
    )
    parser.add_argument(
        "--stage2-export-dir",
        help="Optional override for Stage2 export directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.user_label = _user_suffix(args.user_id)
    if not args.stage1_experiment_name:
        args.stage1_experiment_name = "stage1"
    if not args.stage2_experiment_name:
        args.stage2_experiment_name = f"stage2_{args.user_label}"
    if not args.stage2_model_name:
        args.stage2_model_name = f"EmotionAR_User_{args.user_label}"
    personal_root = _resolve_path(
        args.personal_root,
        PROJECT_DIR / "data" / "personal" / args.user_id,
    )
    if not personal_root.exists():
        raise FileNotFoundError(f"Personal dataset not found: {personal_root}")

    if not args.skip_stage1:
        if args.split_user_data:
            print(f"[DataSplit] Splitting personal data for {args.user_id}")
            split_user_data(
                personal_root,
                train_ratio=args.train_ratio,
                seed=args.split_seed,
            )
            print("[DataSplit] Done.")
        stage1_params = build_stage1_params(args, personal_root)
        print(f"[Stage1] Starting training for {args.user_id}")
        train_stage1.train_experiment(stage1_params)
        print(f"[Stage1] Completed for {args.user_id}")
    else:
        print("[Stage1] Skipped at user request.")

    stage2_params = build_stage2_params(args, personal_root)
    print(f"[Stage2] Starting training for {args.user_id}")
    train_stage2.train_experiment(stage2_params)
    print(f"[Stage2] Completed for {args.user_id}")


if __name__ == "__main__":
    main()
