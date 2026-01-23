# EmotionAR

**Personalized Emotion Recognition in AR via 2-Stage Transfer Learning Pipeline**

ENSF 619 Term Project | University of Calgary

## Overview

EmotionAR addresses facial expression recognition (FER) under HMD occlusion for AR/VR applications. We propose a **2-stage personalization pipeline** that adapts emotion recognition models to individual users.


## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EmotionAR System                         │
├─────────────────────────────────────────────────────────────────┤
│  Unity Application          │  ML Pipeline                      │
│  ├─ STT (Whisper API)       │  ├─ Stage 1: Base Model           │
│  ├─ ChatGPT Conversation    │  └─ Stage 2: User-Specific        │
│  ├─ TTS (OpenAI TTS)        │       Fine-Tuning                 │
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
| **Stage 1** | Base Model | Train EfficientNet-B0 |
| **Stage 2** | User-Specific Fine-Tuning | Fine-tune on Base + Personal data |

### Dataset: EmojiHeroVR 
(https://github.com/thorbenortmann/emoji-hero-vr-database)


### Training Modes Comparison (Stage 2)

#### Accuracy (LOO CV, N=37, 80/20 split)

| Mode | Mean Accuracy | Std Dev | Δ from Base |
|------|---------------|---------|-------------|
| **Training from Scratch (Retrain)** | **86.4%** | ± 8.2% | **+17.0%p** |
| Full Layer Fine-tuning | 80.9% | ± 10.3% | +11.5%p |
| Partial Layer Fine-tuning (Half) | 79.8% | ± 10.3% | +10.4%p |
| Base Model | 69.4% | ± 16.6% | - |

#### Training Time Comparison

| Mode | Mean Time | Notes |
|------|-----------|-------|
| **Base Model Training** | 116.9s ± 23.6s | Stage 1 training time |
| **Training from Scratch** | 112.8s ± 21.6s | ImageNet → new data |
| **Full Layer Fine-tuning** | 70.0s ± 9.2s | **~40% time savings** |
| **Partial Layer Fine-tuning** | 61.0s ± 9.5s | **~46% time savings** |

## Features

### Unity Application
- **STT**: OpenAI Whisper API
- **Conversation**: OpenAI Responses API
- **TTS**: OpenAI TTS API
- **Avatar**: Oculus LipSync

### MLOps
- **MLflow**: Experiment tracking & model registry
- **GitHub Actions**: CI pipeline

## Hardware

| Component | Specification |
|-----------|---------------|
| **GPU** | NVIDIA RTX 4090 (24GB) |
| **CPU** | Intel Core i9-14900K |
| **RAM** | 64GB |