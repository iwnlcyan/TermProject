import timm

def create_model(num_classes: int = 7):
    model = timm.create_model(
        "efficientnet_b0",
        pretrained=True,
        num_classes=num_classes
    )
    return model