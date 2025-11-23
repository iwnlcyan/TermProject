import argparse
import os
from pathlib import Path
from urllib.parse import urlparse
import mlflow
from mlflow import pytorch
from mlflow.tracking import MlflowClient
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from tqdm import tqdm

from src.data_pipeline import get_combined_train_loader, get_dataloaders
from src.model import create_model


def train_experiment(params):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    default_tracking = "sqlite:///C:/Users/chanc/HXI/TermProject/mlflow.db"
    tracking_uri = params.get(
        "tracking_uri", os.getenv("MLFLOW_TRACKING_URI", default_tracking)
    )
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(
        params.get("experiment_name", "emojiherovr_efficientnet_b0_stage1")
    )

    with mlflow.start_run():
        mlflow.log_params(params)

        # Load base model from train.py experiment
        default_stage = params.get("base_model_stage", "Production")
        base_model_name = params.get(
            "base_model_name", f"models:/EmotionAR_Base/{default_stage}"
        )
        try:
            base_model = mlflow.pytorch.load_model(base_model_name)
            mlflow.log_param("base_model_name", base_model_name)
            print(f"Loaded base model from {base_model_name}")
        except Exception as e:
            print(f"Failed to load base model: {e}. Creating new model.")
            # Fallback: create new model if base model not found
            _, _, classes = get_dataloaders(
                data_root=params["base_root"],
                batch_size=params["batch_size"],
                num_workers=params.get("num_workers", 4),
            )
            base_model = create_model(num_classes=len(classes))

        train_loader = get_combined_train_loader(
            base_root=params["base_root"],
            personal_root=params["personal_root"],
            batch_size=params["batch_size"],
            num_workers=params.get("num_workers", 4),
        )

        _, val_loader, classes = get_dataloaders(
            data_root=params["base_root"],
            batch_size=params["batch_size"],
            num_workers=params.get("num_workers", 4),
        )

        model = base_model.to(device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=params["lr"])

        default_early = {
            "metric": "val_loss",
            "mode": "min",
            "patience": 5,
            "min_delta": 1e-3,
        }
        user_cfg = params.get("early_stop")
        if user_cfg is False:
            early_cfg = None
        elif isinstance(user_cfg, dict):
            early_cfg = {**default_early, **user_cfg}
        else:
            early_cfg = default_early

        best_metric = None
        wait = 0
        best_state = None
        if early_cfg:
            mode = early_cfg.get("mode", "min")
            if mode not in {"min", "max"}:
                raise ValueError("early_stop['mode'] must be 'min' or 'max'")
            best_metric = float("inf") if mode == "min" else -float("inf")

        for epoch in range(params["epochs"]):
            # --- Train ---
            model.train()
            train_losses = []
            for images, labels in tqdm(train_loader, desc=f"Epoch {epoch + 1} train"):
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad()
                logits = model(images)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()
                train_losses.append(loss.item())
            mlflow.log_metric(
                "train_loss", sum(train_losses) / len(train_losses), step=epoch
            )

            # --- Validation ---
            model.eval()
            val_losses, all_labels, all_preds = [], [], []
            with torch.no_grad():
                for images, labels in tqdm(val_loader, desc=f"Epoch {epoch + 1} val"):
                    images, labels = images.to(device), labels.to(device)
                    logits = model(images)
                    loss = criterion(logits, labels)
                    val_losses.append(loss.item())

                    preds = logits.argmax(dim=1)
                    all_labels.extend(labels.cpu().numpy())
                    all_preds.extend(preds.cpu().numpy())

            val_loss = sum(val_losses) / len(val_losses)
            val_acc = accuracy_score(all_labels, all_preds)
            val_f1 = f1_score(all_labels, all_preds, average="macro")
            metrics = {"val_loss": val_loss, "val_acc": val_acc, "val_f1": val_f1}

            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_acc", val_acc, step=epoch)
            mlflow.log_metric("val_f1", val_f1, step=epoch)

            print(
                f"[Epoch {epoch + 1}] val_loss={val_loss:.4f}, acc={val_acc:.3f}, f1={val_f1:.3f}"
            )

            if early_cfg:
                metric_key = early_cfg["metric"]
                current = metrics.get(metric_key)
                if current is None:
                    raise ValueError(f"Metric '{metric_key}' is not computed.")
                improved = (
                    current < best_metric - early_cfg["min_delta"]
                    if early_cfg["mode"] == "min"
                    else current > best_metric + early_cfg["min_delta"]
                )
                if improved:
                    best_metric = current
                    wait = 0
                    best_state = {
                        k: v.detach().cpu() for k, v in model.state_dict().items()
                    }
                    mlflow.log_metric("best_" + metric_key, best_metric, step=epoch)
                else:
                    wait += 1
                    if wait >= early_cfg["patience"]:
                        print(f"[EarlyStopping] patience reached at epoch {epoch + 1}")
                        break

        if early_cfg and best_state is not None:
            model.load_state_dict(best_state)
            print("[EarlyStopping] Loaded best model weights before logging.")

        example_inputs, _ = next(iter(train_loader))
        example_inputs = example_inputs[:1].cpu().numpy()
        pytorch.log_model(pytorch_model=model, artifact_path="model")

        parsed = urlparse(mlflow.get_tracking_uri())
        if parsed.scheme in {"sqlite", "mysql", "postgresql"}:
            run_id = mlflow.active_run().info.run_id
            model_name = params.get("model_name", "EmotionAR_Stage1")
            model_stage = params.get("model_stage", "Production")
            mv = mlflow.register_model(f"runs:/{run_id}/model", model_name)
            MlflowClient().transition_model_version_stage(
                name=mv.name,
                version=mv.version,
                stage=model_stage,
                archive_existing_versions=True,
            )
            print(f"[MLflow] Registered {mv.name} v{mv.version} → {model_stage}")

            export_base = params.get(
                "local_export_dir",
                f"./exports/{model_name.lower()}_{model_stage.lower()}",
            )
            export_path = Path(export_base).resolve()
            export_path.mkdir(parents=True, exist_ok=True)
            MlflowClient().download_artifacts(
                run_id=run_id, path="model", dst_path=str(export_path)
            )
            print(f"[MLflow] Exported Stage1 model to {export_path}")
        else:
            print("[INFO] Filesystem tracking backend detected; skipping registry.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user-id",
        required=True,
        help="user folder name under EmotionML/data/personal/, e.g., user_01",
    )
    parser.add_argument(
        "--tracking-uri",
        default="sqlite:///C:/Users/chanc/HXI/TermProject/mlflow.db",
        help="MLflow tracking URI",
    )
    parser.add_argument(
        "--experiment-name",
        default="emojiherovr_efficientnet_b0_stage1",
        help="MLflow experiment name",
    )
    args = parser.parse_args()

    params = {
        "base_root": "C:/Users/chanc/HXI/TermProject/EmotionML/data/emoji-hero-vr-db-si",
        "personal_root": f"C:/Users/chanc/HXI/TermProject/EmotionML/data/personal/{args.user_id}",
        "batch_size": 32,
        "lr": 1e-4,
        "epochs": 50,
        "num_workers": 8,
        "tracking_uri": args.tracking_uri,
        "user_id": args.user_id,
        "experiment_name": args.experiment_name,
    }
    train_experiment(params)
