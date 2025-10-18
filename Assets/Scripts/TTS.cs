using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class TTS : MonoBehaviour
{
    public AudioSource audioSource;

    [Header("OpenAI TTS Settings")]
    [Tooltip("TTS Model: gpt-4o-mini-tts (fast), tts-1 (legacy), tts-1-hd (high quality)")]
    public string model = "gpt-4o-mini-tts";
    
    [Tooltip("Voice: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse")]
    public string voice = "alloy";
    
    [Tooltip("Speed: 0.25 to 4.0")]
    [Range(0.25f, 4.0f)]
    public float speed = 1.0f;

    private object threadLocker = new object();
    private bool audioSourceNeedStop;

    public void PlayText(string _text)
    {
        StartCoroutine(GenerateSpeech(_text));
    }

    private IEnumerator GenerateSpeech(string text)
    {
        var startTime = DateTime.Now;

        // Create request body
        TTSRequest requestBody = new TTSRequest
        {
            model = this.model,
            input = text,
            voice = this.voice,
            speed = this.speed,
            response_format = "mp3"
        };

        string jsonData = JsonUtility.ToJson(requestBody);
        Debug.Log($"Sending TTS request: {jsonData}");

        UnityWebRequest request = new UnityWebRequest("https://api.openai.com/v1/audio/speech", "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", $"Bearer {Credentials.OpenAI_ApiKey}");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            var endTime = DateTime.Now;
            var latency = endTime.Subtract(startTime).TotalMilliseconds;
            Debug.Log($"TTS succeeded! Latency: {latency} ms");

            // Get audio data
            byte[] audioData = request.downloadHandler.data;

            // Convert MP3 to AudioClip
            StartCoroutine(LoadAudioClip(audioData));
        }
        else
        {
            Debug.LogError($"TTS Error: {request.error}\n{request.downloadHandler.text}");
        }

        request.Dispose();
    }

    private IEnumerator LoadAudioClip(byte[] audioData)
    {
        // Save to temporary file
        string tempPath = System.IO.Path.Combine(Application.temporaryCachePath, "tts_temp.mp3");
        System.IO.File.WriteAllBytes(tempPath, audioData);

        // Load using UnityWebRequest (supports MP3 on most platforms)
        using (UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip("file://" + tempPath, AudioType.MPEG))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
                
                if (clip != null)
                {
                    audioSource.clip = clip;
                    audioSource.Play();
                    Debug.Log("Playing TTS audio...");

                    // Wait for audio to finish
                    yield return new WaitWhile(() => audioSource.isPlaying);
                    
                    lock (threadLocker)
                    {
                        audioSourceNeedStop = true;
                    }
                }
                else
                {
                    Debug.LogError("Failed to create AudioClip from MP3 data");
                }
            }
            else
            {
                Debug.LogError($"Failed to load audio: {www.error}");
            }
        }

        // Clean up temp file
        try
        {
            if (System.IO.File.Exists(tempPath))
            {
                System.IO.File.Delete(tempPath);
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning($"Failed to delete temp file: {e.Message}");
        }
    }

    void Update()
    {
        lock (threadLocker)
        {
            if (audioSourceNeedStop)
            {
                audioSource.Stop();
                audioSourceNeedStop = false;
            }
        }
    }

    void OnDestroy()
    {
        // Cleanup if needed
        if (audioSource != null && audioSource.isPlaying)
        {
            audioSource.Stop();
        }
    }

    [System.Serializable]
    private class TTSRequest
    {
        public string model;
        public string input;
        public string voice;
        public float speed;
        public string response_format;
    }
}
