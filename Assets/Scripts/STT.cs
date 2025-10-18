using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;

public class STT : MonoBehaviour
{
    private object threadLocker = new object();
    private string message;

    bool isRecognizedSpeech_OK = false;
    bool isRecognizedSpeech_Error = false;

    private AudioClip recordedClip;
    private bool isRecording = false;
    private string microphoneDevice;

    void Start()
    {
        // Get default microphone
        if (Microphone.devices.Length > 0)
        {
            microphoneDevice = Microphone.devices[0];
            Debug.Log($"Using microphone: {microphoneDevice}");
        }
        else
        {
            Debug.LogError("No microphone detected!");
        }
    }

    public void ButtonClick()
    {
        if (!isRecording)
        {
            StartRecording();
        }
        else
        {
            StopRecording();
        }
    }

    private void StartRecording()
    {
        if (string.IsNullOrEmpty(microphoneDevice))
        {
            SetError("No microphone available");
            return;
        }

        isRecording = true;
        // Record for up to 10 seconds at 16kHz (Whisper's preferred rate)
        recordedClip = Microphone.Start(microphoneDevice, false, 10, 16000);
        Debug.Log("Recording started...");
    }

    private void StopRecording()
    {
        if (!isRecording) return;

        isRecording = false;
        int position = Microphone.GetPosition(microphoneDevice);
        Microphone.End(microphoneDevice);

        // Trim the audio clip to actual recorded length
        float[] samples = new float[position * recordedClip.channels];
        recordedClip.GetData(samples, 0);

        AudioClip trimmedClip = AudioClip.Create("TrimmedClip", position, recordedClip.channels, recordedClip.frequency, false);
        trimmedClip.SetData(samples, 0);

        Debug.Log("Recording stopped. Sending to OpenAI Whisper...");
        StartCoroutine(SendToWhisper(trimmedClip));
    }

    private IEnumerator SendToWhisper(AudioClip clip)
    {
        // Convert AudioClip to WAV bytes
        byte[] wavData = ConvertAudioClipToWav(clip);

        // Create multipart form data
        List<IMultipartFormSection> formData = new List<IMultipartFormSection>();
        formData.Add(new MultipartFormFileSection("file", wavData, "audio.wav", "audio/wav"));
        formData.Add(new MultipartFormDataSection("model", "whisper-1"));
        formData.Add(new MultipartFormDataSection("language", "en")); // Change if needed

        UnityWebRequest request = UnityWebRequest.Post("https://api.openai.com/v1/audio/transcriptions", formData);
        request.SetRequestHeader("Authorization", $"Bearer {Credentials.OpenAI_ApiKey}");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            string responseText = request.downloadHandler.text;
            Debug.Log($"Whisper Response: {responseText}");

            try
            {
                WhisperResponse response = JsonUtility.FromJson<WhisperResponse>(responseText);
                lock (threadLocker)
                {
                    message = response.text;
                    isRecognizedSpeech_OK = true;
                }
            }
            catch (Exception e)
            {
                SetError($"Failed to parse response: {e.Message}");
            }
        }
        else
        {
            SetError($"Whisper API Error: {request.error}\n{request.downloadHandler.text}");
        }

        request.Dispose();
    }

    private void SetError(string errorMessage)
    {
        lock (threadLocker)
        {
            message = errorMessage;
            isRecognizedSpeech_Error = true;
        }
        Debug.LogError(errorMessage);
    }

    private byte[] ConvertAudioClipToWav(AudioClip clip)
    {
        float[] samples = new float[clip.samples * clip.channels];
        clip.GetData(samples, 0);

        Int16[] intData = new Int16[samples.Length];
        Byte[] bytesData = new Byte[samples.Length * 2];

        int rescaleFactor = 32767;

        for (int i = 0; i < samples.Length; i++)
        {
            intData[i] = (short)(samples[i] * rescaleFactor);
            Byte[] byteArr = BitConverter.GetBytes(intData[i]);
            byteArr.CopyTo(bytesData, i * 2);
        }

        int subchunk1Size = 16;
        int subchunk2Size = bytesData.Length;
        int chunkSize = 4 + (8 + subchunk1Size) + (8 + subchunk2Size);

        using (MemoryStream stream = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(stream))
        {
            // RIFF header
            writer.Write(System.Text.Encoding.UTF8.GetBytes("RIFF"));
            writer.Write(chunkSize);
            writer.Write(System.Text.Encoding.UTF8.GetBytes("WAVE"));

            // fmt subchunk
            writer.Write(System.Text.Encoding.UTF8.GetBytes("fmt "));
            writer.Write(subchunk1Size);
            writer.Write((ushort)1); // Audio format (1 = PCM)
            writer.Write((ushort)clip.channels);
            writer.Write(clip.frequency);
            writer.Write(clip.frequency * clip.channels * 2); // Byte rate
            writer.Write((ushort)(clip.channels * 2)); // Block align
            writer.Write((ushort)16); // Bits per sample

            // data subchunk
            writer.Write(System.Text.Encoding.UTF8.GetBytes("data"));
            writer.Write(subchunk2Size);
            writer.Write(bytesData);

            return stream.ToArray();
        }
    }

    void Update()
    {
        if (isRecognizedSpeech_OK)
        {
            isRecognizedSpeech_OK = false;
            Manager._OnSSTResponse_OK(message);
        }
        if (isRecognizedSpeech_Error)
        {
            isRecognizedSpeech_Error = false;
            Manager._OnSSTResponse_ERROR(message);
        }
    }

    [System.Serializable]
    private class WhisperResponse
    {
        public string text;
    }
}
