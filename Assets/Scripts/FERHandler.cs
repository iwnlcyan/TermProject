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
/// Handles the Facial Emotion Recognition (FER) processes, including capturing images, sending them for analysis, and processing the results.
/// </summary>
public class FerHandler : MonoBehaviour
{
    private FaceExpressionHandler _faceExpressionHandler;
    
    /// <summary>Flag to determine if facial emotion recognition should be done periodically.</summary>
    // If true, images are sent for FER processing at regular intervals. If false, images are sent on specific events.
    [SerializeField] private bool PeriodicalFerMode = true;
    [SerializeField] private int PeriodicalFPS = 5;

    // Coroutine for continuous facial emotion recognition
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
    
    // Callback for when an emote enters the action area, triggers the facial emotion recognition
    private void EmoteEnteredActionAreaCallback(Emoji emoji) => SendRestImage();

    /// <summary>
    /// Initiates the sending of REST images for FER processing.
    /// </summary>
    private void SendRestImage()
    {        
        if (!PeriodicalFerMode)
            StartCoroutine(PostRestImage());    // Send a single image for FER processing.
        else if (_coroutine == null)
            _coroutine = StartCoroutine(SendRestImageContinuous());     // Start the continuous image sending process.
    }
    
    /// <summary>
    /// Coroutine for continuously sending images at a specified interval for FER processing.
    /// </summary>
    private IEnumerator SendRestImageContinuous()
    {
        // Wait until the end of frame to ensure all events are processed and EmojisAreInActionArea is true
        yield return new WaitForEndOfFrame();

        // Interval between each image sent for FER processing.
        float interval = 1f / PeriodicalFPS;
        float nextPostTime = Time.realtimeSinceStartup + interval;
        
        while (PeriodicalFerMode && GameManager.Instance.LevelProgress.EmojisAreInActionArea)
        {
            // Log a new FER request.
            EditorUIFerStats.Instance.LogNewRestRequest();
            
            // Send an image for FER processing.
            StartCoroutine(PostRestImage());

            // Calculate time needed to wait to ensure periodic execution
            float waitTime = Math.Max(nextPostTime - Time.realtimeSinceStartup, 0);
            yield return new WaitForSecondsRealtime(waitTime);

            // iterate timer to next interval
            nextPostTime += interval;
        }
        
        _coroutine = null;
    }

    /// <summary>
    /// Captures a webcam frame, converts it to base64, and sends it for FER processing.
    /// </summary>
    private IEnumerator PostRestImage()
    {
        Snapshot snapshot = WebcamManager.GetSnapshot();
        
        while (snapshot == null)
        {
            yield return null;
            snapshot = WebcamManager.GetSnapshot();
        }
        
        // Initialize log data for the current FER process.
        LogData logData = new()
        {
            Timestamp = snapshot.Timestamp,
            LevelID = GameManager.Instance.Level.LevelName,
            Emoji = GameManager.Instance.LevelProgress.GetEmojiInActionArea,
            UserID = EditorUI.EditorUI.Instance.UserID,
            FaceExpressions = LoggingSystem.Instance.LogFaceExpressions? _faceExpressionHandler.GetFaceExpressionsAsJson() : null
        };
        
        // Convert the captured image to base64 format.
        string image = WebcamManager.GetBase64(snapshot);
        yield return null;  // Wait until the next frame to reduce lag

        // Send the base64 image for FER processing.
        Rest.PostBase64(image, logData, this);
    }
    
    /// <summary>
    /// Processes the REST response from the FER API.
    /// </summary>
    /// <param name="response">The JSON response from the FER service.</param>
    /// <param name="logData">The log data associated with the current FER process.</param>
    public void ProcessRestResponse(string response, LogData logData)
    {
        // Parse the JSON response to get FER probabilities.
        logData.FerProbabilities = JsonUtility.FromJson<Probabilities>(response);
        // Determine the emotion with the highest probability.
        logData.EmoteFer = GetEmoteWithHighestProbability(logData.FerProbabilities);
        // Trigger an event for the detected emotion.
        EventManager.InvokeEmotionDetected(logData.EmoteFer);
        
        HandleFerCompletion(logData);
    }

    /// <summary>
    /// Handles errors that occur during the REST call for FER processing.
    /// </summary>
    /// <param name="error">The exception thrown during the REST call.</param>
    /// <param name="logData">The log data associated with the current FER process.</param>
    public void ProcessRestError(Exception error, LogData logData)
    {
        // Log the error message.
        Debug.LogWarning("REST Error: " + error.Message);
        
        // Set FER probabilities to default (zero) values.
        logData.FerProbabilities = new Probabilities();
        
        HandleFerCompletion(logData);
    }

    private void HandleFerCompletion(LogData logData)
    {
        // Log the FER results if it is not of type Training.
        if (LoggingSystem.Instance.LogTrainingLevel || GameManager.Instance.Level.LevelMode != ELevelMode.Training)
            LoggingSystem.Instance.AddToLogDataList(logData);
        
        // Update the UI with the FER results.
        EditorUIFerStats.Instance.LogRestResponse(logData);

        // If emojis are still in the action area, continue the FER process.
        if (GameManager.Instance.LevelProgress.EmojisAreInActionArea)
            SendRestImage();
    }
    
    /// <summary>
    /// Determines the emotion with the highest probability from the FER results.
    /// </summary>
    /// <param name="probabilities">The FER probabilities for each emotion.</param>
    /// <returns>The emotion with the highest probability.</returns>
    private static EEmote GetEmoteWithHighestProbability(Probabilities probabilities)
    {
        // Map each emotion to its probability.
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

        // Return the emotion with the highest probability.
        return result.OrderByDescending(kv => kv.Value).First().Key;
    }
}

