# Copyright 2022 Andrey Savchenko
# https://github.com/HSE-asavchenko/hsemotion-onnx/blob/bd8a9882924b38e859ae7801305ae203cd71acc1/hsemotion_onnx/facial_emotions.py
# Copyright for modifications 2023 Thorben Ortmann

# Licensed under the Apache License, Version 2.0 (the "License");

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


class HSEmotionRecognizer:
    def __init__(self):
        self.model_name = 'enet_b2_7'
        self.img_size = 260
        self.emotion_labels = ['anger', 'disgust', 'fear', 'happiness', 'neutral', 'sadness', 'surprise']

        path = f'{Path(__file__).parent / self.model_name}.onnx'
        self.ort_session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        :param image: numpy array of shape (height, width, channels)
        :return: numpy array of shape (1, channels, height, width)
        """
        x = cv2.resize(image, (self.img_size, self.img_size)) / 255
        # Normalize color channels
        x[..., 0] = (x[..., 0] - 0.485) / 0.229
        x[..., 1] = (x[..., 1] - 0.456) / 0.224
        x[..., 2] = (x[..., 2] - 0.406) / 0.225
        return x.transpose(2, 0, 1).astype("float32")[np.newaxis, ...]

    def predict_emotions(self, face_img: np.ndarray) -> list[float]:
        """
        :param face_img: numpy array of shape (height, width, channels)
        :return: probability scores in the following order:
            0: 'Anger', 1: 'Disgust', 2: 'Fear', 3: 'Happiness', 4: 'Neutral', 5: 'Sadness', 6: 'Surprise'
        """
        e_scores = self.ort_session.run(None, {"input": self.preprocess(face_img)})[0][0]
        x = e_scores
        e_x = np.exp(x - np.max(x)[np.newaxis])
        e_x = e_x / e_x.sum()[None]
        return e_x.tolist()



# from pathlib import Path
# import torch
# import torch.nn.functional as F
# from torchvision import transforms
# import cv2
# import numpy as np

# class HSEmotionRecognizer:
#     def __init__(self, model_name="model.pth", device="cpu"):
#         """
#         :param model_name: filename of the PyTorch .pth model in the same folder as this script
#         :param device: "cpu" or "cuda"
#         """
#         self.device = torch.device(device)

#         # Use relative path based on this script's location
#         script_dir = Path(__file__).parent
#         model_path = script_dir / model_name

#         if not model_path.exists():
#             raise FileNotFoundError(f"Model file not found: {model_path}")

#         # Load the model
#         self.model = torch.load(model_path, map_location=self.device, weights_only=False)
#         self.model.eval()

#         self.img_size = 260
#         self.emotion_labels = ['anger', 'disgust', 'fear', 'happiness', 'neutral', 'sadness', 'surprise']

#         self.transform = transforms.Compose([
#             transforms.ToPILImage(),
#             transforms.Resize((self.img_size, self.img_size)),
#             transforms.ToTensor(),
#             transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
#         ])

#     def preprocess(self, image: np.ndarray) -> torch.Tensor:
#         x = self.transform(image)
#         return x.unsqueeze(0).to(self.device)

#     def predict_emotions(self, face_img: np.ndarray) -> list[float]:
#         x = self.preprocess(face_img)
#         with torch.no_grad():
#             logits = self.model(x)
#             probs = F.softmax(logits, dim=1)
#         return probs.squeeze(0).cpu().tolist()
