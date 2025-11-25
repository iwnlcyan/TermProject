import os
import random
from PIL import Image
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, ConcatDataset


class RandomHMDMask:
    """Approximate HMD occlusion by masking the upper face region."""

    def __init__(self, p: float = 0.5, band_ratio=(0.35, 0.55)):
        self.p = p
        self.band_ratio = band_ratio

    def __call__(self, img: Image.Image):
        if random.random() > self.p:
            return img
        width, height = img.size
        band_height = int(height * random.uniform(*self.band_ratio))
        mask = Image.new("RGB", (width, band_height), (0, 0, 0))
        img = img.copy()
        img.paste(mask, (0, 0))
        return img

train_tf = transforms.Compose(
    [
        transforms.RandomResizedCrop(256, scale=(0.8, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomApply(
            [
                transforms.ColorJitter(0.2, 0.2, 0.2, 0.1),
                transforms.RandomGrayscale(p=0.2),
                transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 1.5)),
            ],
            p=0.5,
        ),
        transforms.RandomAffine(degrees=12, translate=(0.05, 0.05), shear=5),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        RandomHMDMask(p=0.5),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.4, scale=(0.02, 0.15), ratio=(0.3, 3.3)),
    ]
)

val_tf = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
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
