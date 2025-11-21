import os
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, ConcatDataset

train_tf = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

val_tf = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

def get_dataloaders(data_root: str, batch_size: int = 32, num_workers: int = 8):
    train_dir = os.path.join(data_root, "training_set")
    val_dir = os.path.join(data_root, "validation_set")

    train_ds = datasets.ImageFolder(train_dir, transform=train_tf)
    val_ds = datasets.ImageFolder(val_dir, transform=val_tf)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    return train_loader, val_loader, train_ds.classes


def get_personal_dataloaders(personal_root: str, batch_size: int = 16, num_workers: int = 2):
    train_loader, val_loader, classes = get_dataloaders(
        data_root=personal_root, batch_size=batch_size, num_workers=num_workers
    )
    return train_loader, val_loader, classes


def get_combined_train_loader(base_root, personal_root, batch_size=32, num_workers=4):
    base_ds = datasets.ImageFolder(
        os.path.join(base_root, "training_set"), transform=train_tf
    )
    personal_ds = datasets.ImageFolder(
        os.path.join(personal_root, "training_set"), transform=train_tf
    )
    combined = ConcatDataset([base_ds, personal_ds])
    return DataLoader(combined, batch_size=batch_size, shuffle=True, num_workers=num_workers)
