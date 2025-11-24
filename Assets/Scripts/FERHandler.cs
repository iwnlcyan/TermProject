using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Data;
using Enums;
using Manager;
using Systems;
using UnityEngine;
using Utilities;

/// <summary>
/// Handles the Facial Emotion Recognition (FER) processes,
/// including capturing images, sending them for analysis,
/// and computing the most probable emotion in a time window.
/// </summary>
public class FerHandler : MonoBehaviour
{
    private FaceExpressionHandler _faceExpressionHandler;

    [SerializeField] private bool PeriodicalFerMode = true;
    [SerializeField] private int PeriodicalFPS = 5;

    /// <summary>
    /// Time window (in seconds) to average predictions over.
    /// Example: 1.5 seconds = stable FER output
    /// </summary>
    [SerializeField] private float FerWindowSeconds = 1.5f;

    // Where we store recent FER outputs
    private readonly List<(float time, Probabilities probs)> _ferWindow =
        new List<(float time, Probabilities probs)>();

    [SerializeField] public EEmote CurrentWindowEmotion { get; private set; } = EEmote.Neutral;

    // Coroutine reference
    private Coroutine _coroutine;

    private void Start()
    {
        _faceExpressionHandler = new FaceExpressionHandler();
        EventManager.OnEmoteEnteredActionArea += EmoteEnteredActionAreaCallback;
    }

    private void OnDestroy()
    {
        EventManager.OnEmoteEnteredActionArea -= EmoteEnteredActionAreaCallback;
    }

    private void EmoteEnteredActionAreaCallback(Emoji emoji) => SendRestImage();

    private void SendRestImage()
    {
        if (!PeriodicalFerMode)
            StartCoroutine(PostRestImage());
        else if (_coroutine == null)
            _coroutine = StartCoroutine(SendRestImageContinuous());
    }

    private IEnumerator SendRestImageContinuous()
    {
        yield return new WaitForEndOfFrame();

        float interval = 1f / PeriodicalFPS;
        float nextPostTime = Time.realtimeSinceStartup + interval;

        while (PeriodicalFerMode && GameManager.Instance.LevelProgress.EmojisAreInActionArea)
        {
            EditorUIFerStats.Instance.LogNewRestRequest();
            StartCoroutine(PostRestImage());

            float waitTime = Mathf.Max(nextPostTime - Time.realtimeSinceStartup, 0);
            yield return new WaitForSecondsRealtime(waitTime);

            nextPostTime += interval;
        }

        _coroutine = null;
    }

    private IEnumerator PostRestImage()
    {
        Snapshot snapshot = WebcamManager.GetSnapshot();

        while (snapshot == null)
        {
            yield return null;
            snapshot = WebcamManager.GetSnapshot();
        }

        LogData logData = new()
        {
            Timestamp = snapshot.Timestamp,
            LevelID = GameManager.Instance.Level.LevelName,
            Emoji = GameManager.Instance.LevelProgress.GetEmojiInActionArea,
            UserID = EditorUI.EditorUI.Instance.UserID,
            FaceExpressions = LoggingSystem.Instance.LogFaceExpressions
                ? _faceExpressionHandler.GetFaceExpressionsAsJson()
                : null
        };

        string image = WebcamManager.GetBase64(snapshot);
        yield return null;

        Rest.PostBase64(image, logData, this);
    }

    // ----------------------------------------------------------------------
    // NEW: Time-window FER aggregation
    // ----------------------------------------------------------------------

    public void ProcessRestResponse(string response, LogData logData)
    {
        Probabilities probs = JsonUtility.FromJson<Probabilities>(response);
        logData.FerProbabilities = probs;

        // Add current result to window
        float now = Time.realtimeSinceStartup;
        _ferWindow.Add((now, probs));

        // Remove predictions older than window length
        _ferWindow.RemoveAll(entry => now - entry.time > FerWindowSeconds);

        // Compute aggregated prediction
        Probabilities averaged = ComputeAverageProbabilities();
        logData.EmoteFer = GetEmoteWithHighestProbability(averaged);
        CurrentWindowEmotion = logData.EmoteFer;   // <--- update the public variable


        // Fire event based on window-averaged emotion
        EventManager.InvokeEmotionDetected(logData.EmoteFer);

        HandleFerCompletion(logData);
    }

    public void ProcessRestError(Exception error, LogData logData)
    {
        Debug.LogWarning("REST Error: " + error.Message);
        logData.FerProbabilities = new Probabilities();
        HandleFerCompletion(logData);
    }

    private Probabilities ComputeAverageProbabilities()
    {
        if (_ferWindow.Count == 0)
            return new Probabilities();

        float anger = 0, disgust = 0, fear = 0, happiness = 0, neutral = 0, sadness = 0, surprise = 0;

        foreach (var entry in _ferWindow)
        {
            anger += entry.probs.anger;
            disgust += entry.probs.disgust;
            fear += entry.probs.fear;
            happiness += entry.probs.happiness;
            neutral += entry.probs.neutral;
            sadness += entry.probs.sadness;
            surprise += entry.probs.surprise;
        }

        float count = _ferWindow.Count;

        return new Probabilities
        {
            anger = anger / count,
            disgust = disgust / count,
            fear = fear / count,
            happiness = happiness / count,
            neutral = neutral / count,
            sadness = sadness / count,
            surprise = surprise / count
        };
    }

    private void HandleFerCompletion(LogData logData)
    {
        if (LoggingSystem.Instance.LogTrainingLevel ||
            GameManager.Instance.Level.LevelMode != ELevelMode.Training)
            LoggingSystem.Instance.AddToLogDataList(logData);

        EditorUIFerStats.Instance.LogRestResponse(logData);

        if (GameManager.Instance.LevelProgress.EmojisAreInActionArea)
            SendRestImage();
    }

    private static EEmote GetEmoteWithHighestProbability(Probabilities probabilities)
    {
        Dictionary<EEmote, float> result = new()
        {
            { EEmote.Anger, probabilities.anger },
            { EEmote.Disgust, probabilities.disgust },
            { EEmote.Fear, probabilities.fear },
            { EEmote.Happiness, probabilities.happiness },
            { EEmote.Neutral, probabilities.neutral },
            { EEmote.Sadness, probabilities.sadness },
            { EEmote.Surprise, probabilities.surprise }
        };

        return result.OrderByDescending(kv => kv.Value).First().Key;
    }
}


