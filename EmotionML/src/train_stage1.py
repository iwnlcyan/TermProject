import mlflow
from mlflow import pytorch
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from tqdm import tqdm

from src.data_pipeline import get_combined_train_loader, get_dataloaders
from src.model import create_model


def train_experiment(params):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("emojiherovr_efficientnet_b0_stage1")

    with mlflow.start_run():
        mlflow.log_params(params)

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

        model = create_model(num_classes=len(classes)).to(device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=params["lr"])

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

            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_acc", val_acc, step=epoch)
            mlflow.log_metric("val_f1", val_f1, step=epoch)

            print(
                f"[Epoch {epoch + 1}] val_loss={val_loss:.4f}, acc={val_acc:.3f}, f1={val_f1:.3f}"
            )

        example_inputs, _ = next(iter(train_loader))
        example_inputs = example_inputs[:1].cpu().numpy()
        pytorch.log_model(model=model, name="model", input_example=example_inputs)


if __name__ == "__main__":
    params = {
        "base_root": "/Users/myungjunlee/Library/Mobile Documents/com~apple~CloudDocs/Desktop/TermProject/EmotionML/data/emoji-hero-vr-db-si",
        "personal_root": "/Users/myungjunlee/Library/Mobile Documents/com~apple~CloudDocs/Desktop/TermProject/EmotionML/data/personal/user_01",
        "batch_size": 32,
        "lr": 1e-4,
        "epochs": 2,
        "num_workers": 8,
    }
    train_experiment(params)
