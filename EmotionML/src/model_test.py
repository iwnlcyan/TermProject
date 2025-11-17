from src.model import create_model
model = create_model(num_classes=7)
print(type(model))
print(model.classifier)