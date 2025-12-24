# EmotionAR

**Personalized Emotion Recognition in AR via MLOps Pipeline**

ENSF 619 Term Project | University of Calgary

## 📖 Overview

EmotionAR is a research project addressing facial expression recognition (FER) under HMD (Head-Mounted Display) occlusion for AR/VR applications. We propose a **3-stage personalization pipeline** that adapts emotion recognition models to individual users.

### Research Questions

- **RQ1**: How can facial expression support personalized VR emotion recognition without biosensors?
- **RQ2**: Does personalization improve recognition across user differences?
- **RQ3**: How can SE practices facilitate emotion recognition?

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EmotionAR System                         │
├─────────────────────────────────────────────────────────────────┤
│  Unity Application          │  ML Pipeline                      │
│  ├─ STT (Whisper API)       │  ├─ Stage 0: Base Model           │
│  ├─ ChatGPT Conversation    │  ├─ Stage 1: Model Reinforcement  │
│  ├─ TTS (OpenAI TTS)        │  └─ Stage 2: Personalization      │
│  └─ Avatar Lip Sync         │                                   │
├─────────────────────────────────────────────────────────────────┤
│  MLOps                                                          │
│  ├─ MLflow: Experiment Tracking & Model Registry                │
│  └─ GitHub Actions: CI Pipeline                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 ML Pipeline

### 3-Stage Personalization Strategy

| Stage | Description | Purpose |
|-------|-------------|---------|
| **Stage 0** | Base Model | Train EfficientNet-B0 on EmojiHeroVR dataset |
| **Stage 1** | Model Reinforcement | Fine-tune on combined base + personal data |
| **Stage 2** | Personal Specialization | Freeze backbone, fine-tune classifier only |

### Dataset: EmojiHeroVR 
(https://github.com/thorbenortmann/emoji-hero-vr-database)

| Attribute | Value |
|-----------|-------|
| Total Participants | 37 |
| Total Images | 3,556 |
| Emotion Classes | 7 |
| Training Set | 21 participants |
| Validation Set | 8 participants |
| Test Set | 8 participants |

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| Batch Size | 32 |
| Learning Rate | 1e-4 |
| Optimizer | Adam |
| Loss Function | Cross-Entropy |
| Epochs (Stage 0) | 10 |
| Epochs (Stage 1, 2) | 2 |
| Backbone Freezing | EfficientNet backbone frozen in Stage 2 |

### Results

| Stage | Validation Accuracy | Description |
|-------|---------------------|-------------|
| Stage 0 | 69.6% | Base model |
| Stage 1 | 70.7% | Reinforced model |
| Stage 2 | **72.7%** | Personalized model |

## 🚀 Features

### Unity Application
- **STT (Speech-to-Text)**: OpenAI Whisper API
- **ChatGPT Conversation**: OpenAI Responses API
- **TTS (Text-to-Speech)**: OpenAI TTS API
- **Avatar Lip Sync**: Oculus LipSync

### MLOps
- **MLflow**: Model versioning, experiment tracking, model registry for 3-stage pipeline dependency management
- **GitHub Actions**: Automated CI for model testing on new data arrival

## 👥 Authors

- **Myungjun Lee** (30301722) - mj.lee1@ucalgary.ca
- **Chuyang Zhang** (30290069) - chuyang.zhang1@ucalgary.ca
