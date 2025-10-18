# EmotionAR

Unity project: Voice-enabled AI Avatar conversation system using OpenAI APIs

## 🚀 Features

- **STT (Speech-to-Text)**: OpenAI Whisper API
- **ChatGPT Conversation**: OpenAI Responses API
- **TTS (Text-to-Speech)**: OpenAI TTS API
- **Avatar Lip Sync**: Oculus LipSync

## 📋 Requirements

- Unity 2022.2.18f1
- OpenAI API Key

## ⚙️ Setup

### 1. API Key Configuration

1. Copy `Assets/Scripts/Credentials.cs.template` to `Credentials.cs`
2. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
3. Replace `YOUR_OPENAI_API_KEY_HERE` in `Credentials.cs` with your actual API key

```csharp
public const string OpenAI_ApiKey = "sk-proj-your-actual-key-here";
```

### 2. Run Project

1. Open project in Unity
2. Open `SampleScene`
3. Press Play button
4. **Space bar**: Start/Stop recording

## 🎮 Usage

1. **Press Space once**: Start recording (red indicator)
2. **Press Space again**: Stop recording and send to API (blue indicator)
3. ChatGPT responds with TTS audio playback
4. Avatar lip sync animation plays

## 📁 Key Files

- `Assets/Scripts/STT.cs` - Speech recognition
- `Assets/Scripts/TTS.cs` - Speech synthesis
- `Assets/Scripts/Manager.cs` - Main flow controller
- `Assets/Scripts/GPT_Personality.cs` - Character persona
- `Assets/ChatGPT-Wrapper-For-Unity-main/` - ChatGPT API wrapper
