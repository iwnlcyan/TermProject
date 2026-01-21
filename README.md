# EmotionAR

**Personalized Emotion Recognition in AR via MLOps Pipeline**

ENSF 619 Term Project | University of Calgary

## Overview

EmotionAR addresses facial expression recognition (FER) under HMD occlusion for AR/VR applications. We propose a **2-stage personalization pipeline** that adapts emotion recognition models to individual users.

### Research Questions

- **RQ1**: Can FER achieve acceptable accuracy with HMD-occluded faces?
- **RQ2**: Does personalization fine-tuning improve accuracy over general models?

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EmotionAR System                         │
├─────────────────────────────────────────────────────────────────┤
│  Unity Application          │  ML Pipeline                      │
│  ├─ STT (Whisper API)       │  ├─ Stage 1: Base Model           │
│  ├─ ChatGPT Conversation    │  └─ Stage 2: Personalization      │
│  ├─ TTS (OpenAI TTS)        │                                   │
│  └─ Avatar Lip Sync         │                                   │
├─────────────────────────────────────────────────────────────────┤
│  MLOps                                                          │
│  ├─ MLflow: Experiment Tracking & Model Registry                │
│  └─ GitHub Actions: CI Pipeline                                 │
└─────────────────────────────────────────────────────────────────┘
```

## ML Pipeline

### 2-Stage Personalization Strategy

| Stage | Description | Details |
|-------|-------------|---------|
| **Stage 1** | Base Model | Train EfficientNet-B0 on 28 users (lr=1e-4) |
| **Stage 2** | Personalize | Fine-tune with Base + Personal data (lr=1e-5) |

### Dataset: EmojiHeroVR 
(https://github.com/thorbenortmann/emoji-hero-vr-database)

| Attribute | Value |
|-----------|-------|
| Total Participants | 37 |
| Total Images | 3,556 |
| Emotion Classes | 7 (Anger, Disgust, Fear, Happiness, Neutral, Sadness, Surprise) |
| LOO CV Split | 28 Train / 8 Val / 1 Test (per fold) |
| Personal Data Split | 80% Calibration / 20% Test |

### Hyperparameters

| Parameter | Stage 1 | Stage 2 |
|-----------|---------|---------|
| Learning Rate | 1e-4 | 1e-5 |
| Batch Size | 32 | 32 |
| Optimizer | Adam | Adam |

### Results (LOO CV, N=37)

| Stage | Accuracy | Description |
|-------|----------|-------------|
| Stage 1 (Base) | 71.0% ± 13.8% | General model |
| Stage 2 (Personalize) | **81.8% ± 9.2%** | +10.8%p improvement |

## Features

### Unity Application
- **STT**: OpenAI Whisper API
- **Conversation**: OpenAI Responses API
- **TTS**: OpenAI TTS API
- **Avatar**: Oculus LipSync

### MLOps
- **MLflow**: Experiment tracking & model registry
- **GitHub Actions**: CI pipeline
