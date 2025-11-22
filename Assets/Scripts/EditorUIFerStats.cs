using System;
using System.Diagnostics.CodeAnalysis;
using Data;
using Manager;
using UnityEngine;
using Utilities;

[SuppressMessage("ReSharper", "NotAccessedField.Global")]
// Must be of type MonoBehaviour for Editor UI binding functionality
public class EditorUIFerStats : Singleton<EditorUIFerStats>
{
    // Time of the last REST POST request
    private DateTime _postTime;
    
    // Public properties to be displayed in the Editor UI
    [SerializeField, HideInInspector] public int CurrentActiveRestPosts;     // Current number of active REST POST requests.
    [SerializeField, HideInInspector] public int TotalPosts;    // Total number of REST POST requests made.
    [SerializeField, HideInInspector] public double CurrentPostsFPS;    // Frames per second calculated based on the time between the last two REST POST requests.
    [SerializeField, HideInInspector] public string SnapshotFPS;    // Frames per second of the snapshots.
    
    /// <summary>
    /// Called when a new REST POST request is made. Updates the time between posts, calculates the posts per second, and increments the active and total post counters.
    /// </summary>
    internal void LogNewRestRequest()
    {
        TimeSpan postTime = DateTime.Now - _postTime;  // Calculate time since last POST request
        if (postTime.TotalSeconds < 1)  // If less than one second has passed since the last POST request
            CurrentPostsFPS = Math.Round(1 / postTime.TotalSeconds, 1); // Update posts per second
        _postTime = DateTime.Now;  // Update last POST request time
        
        CurrentActiveRestPosts++;  // Increment active POST request counter
        TotalPosts++;  // Increment total POST request counter
    }
    
    /// <summary>
    /// Called when a REST response is received. Updates the UI with the response data and decrements the active post counter.
    /// </summary>
    /// <param name="logData">The log data associated with the REST response.</param>
    internal void LogRestResponse(LogData logData)
    {
        EditorUI.EditorUI.SetRestResponseData(logData);
        CurrentActiveRestPosts--;
    }

    /// <summary>
    /// Resets the total posts counter when a new level is started.
    /// </summary>
    private void NewLevel()
    {
        TotalPosts = 0;
    }

    private void OnEnable()
    {
        EventManager.OnLevelStarted += NewLevel;
    }

    private void OnDisable()
    {
        EventManager.OnLevelStarted -= NewLevel;
    }
}