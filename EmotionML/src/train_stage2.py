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

from src.data_pipeline import get_personal_dataloaders


def train_experiment(params):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    default_tracking = "sqlite:///C:/Users/chanc/HXI/TermProject/mlflow.db"
    tracking_uri = params.get(
        "tracking_uri", os.getenv("MLFLOW_TRACKING_URI", default_tracking)
    )
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(
        params.get("experiment_name", "emojiherovr_efficientnet_b0_stage2")
    )

    stage1_stage = params.get("stage1_model_stage", "Production")
    stage1_name = params.get("stage1_model_name", "EmotionAR_Stage1")
    stage1_uri = params.get(
        "stage1_model_uri", f"models:/{stage1_name}/{stage1_stage}"
    )

    try:
        stage1_model = mlflow.pytorch.load_model(stage1_uri)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load Stage1 model from '{stage1_uri}'. "
            "Ensure Stage1 has been registered correctly."
        ) from exc

    with mlflow.start_run():
        mlflow.log_params(params)
        mlflow.log_param("stage1_model_uri", stage1_uri)

        train_loader, val_loader, classes = get_personal_dataloaders(
            personal_root=params["personal_root"],
            batch_size=params["batch_size"],
            num_workers=params.get("num_workers", 4),
        )

        model = stage1_model.to(device)

        for _, param in model.named_parameters():
            param.requires_grad = False
        for param in model.classifier.parameters():
            param.requires_grad = True
        optimizer = optim.Adam(model.classifier.parameters(), lr=params["lr"])

        criterion = nn.CrossEntropyLoss()

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
            user_id = params.get("user_id", "unknown")
            model_name = params.get("model_name", f"EmotionAR_{user_id}")
            model_stage = params.get("model_stage", "Production")
            mv = mlflow.register_model(f"runs:/{run_id}/model", model_name)
            MlflowClient().transition_model_version_stage(
                name=mv.name,
                version=mv.version,
                stage=model_stage,
                archive_existing_versions=False,
            )
            print(f"[MLflow] Registered {mv.name} v{mv.version} → {model_stage}")

            export_base = params.get(
                "local_export_dir",
                f"./exports/{model_name.lower()}_{model_stage.lower()}",
            )
            export_path = Path(export_base).resolve()
            export_path.mkdir(parents=True, exist_ok=True)
            client = MlflowClient()
            client.download_artifacts(
                run_id=run_id, path="model", dst_path=str(export_path)
            )
            print(f"[MLflow] Exported best model artifacts to {export_path}")
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
        default="emojiherovr_efficientnet_b0_stage2",
        help="MLflow experiment name",
    )
    args = parser.parse_args()

    params = {
        "personal_root": f"C:/Users/chanc/HXI/TermProject/EmotionML/data/personal/{args.user_id}",
        "batch_size": 32,
        "lr": 1e-4,
        "epochs": 50,
        "num_workers": 8,
        "user_id": args.user_id,
        "tracking_uri": args.tracking_uri,
        "experiment_name": args.experiment_name,
    }
    train_experiment(params)
