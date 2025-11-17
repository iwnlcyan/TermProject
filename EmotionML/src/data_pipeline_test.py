from src.data_pipeline import get_dataloaders

if __name__ == "__main__":
    data_root = "/Users/myungjunlee/Library/Mobile Documents/com~apple~CloudDocs/Desktop/TermProject/EmotionML/data/emoji-hero-vr-db-si"
    train_loader, val_loader, classes = get_dataloaders(
        data_root, batch_size=4, num_workers=0  # test code
    )

    print(classes)
    images, labels = next(iter(train_loader))
    print(images.shape)
    print(labels)