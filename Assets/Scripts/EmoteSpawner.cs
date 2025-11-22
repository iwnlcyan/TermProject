using System.Collections;
using System.Collections.Generic;
using Enums;
using Manager;
using UnityEngine;
using Utilities;
using Random = UnityEngine.Random;

/// <summary>
/// This class is responsible for spawning emotes in the game. It allows for emotes to be spawned at specific locations based on the game's level and mode.
/// </summary>
public class EmoteSpawner : MonoBehaviour
{
    [SerializeField] private Transform EmojiSpawnPosition; // The GameObject indicating the spawn position
    [SerializeField] private float XWidth = 0.5f; // The width between lanes for emote spawning.
    [SerializeField] private int Lanes = 4; // The number of lanes where emotes can be spawned.

    private bool _spawnActive; // Flag to control whether emotes should be spawned.

    private readonly List<Vector3> _spawnLocations = new(); // List of possible locations for emote spawning.
    private Vector3 _actionAreaSpawnLocation; // Specific location to spawn emotes during Training mode.

    private static ObjectPool _objectPool;


    private void OnEnable()
    {
        EventManager.OnLevelStarted += OnLevelStartedCallback;
        EventManager.OnLevelFinished += OnLevelFinishedCallback;
        EventManager.OnLevelStopped += OnLevelStoppedCallback;
        EventManager.OnEmoteFulfilled += OnEmoteFulfilledCallback;
        EventManager.OnEmoteFailed += OnEmoteFailedCallback;
    }

    private void OnDisable()
    {
        EventManager.OnLevelStarted -= OnLevelStartedCallback;
        EventManager.OnLevelFinished -= OnLevelFinishedCallback;
        EventManager.OnLevelStopped -= OnLevelStoppedCallback;
        EventManager.OnEmoteFulfilled -= OnEmoteFulfilledCallback;
        EventManager.OnEmoteFailed -= OnEmoteFailedCallback;
    }

    private void Start()
    {
        _objectPool = GetComponent<ObjectPool>();
        
        // Calculate and store possible emote spawn locations based on lanes and width.
        Vector3 spawnDistance = EmojiSpawnPosition.position;
        for (int lane = 0; lane < Lanes; lane++)
        {
            float offset = (Lanes - 1) / 2f;
            _spawnLocations.Add(spawnDistance + new Vector3((lane - offset) * XWidth, 0, 0));
        }
        
        // Define a specific spawn location for the Training mode.
        _actionAreaSpawnLocation = GameManager.Instance.ActionAreaTransform.position + GameManager.Instance.ActionAreaTransform.up * 0.15f;
    }

    /// <summary>
    /// Start spawning emotes when the level starts.
    /// </summary>
    private void OnLevelStartedCallback()
    {
        _spawnActive = true;
        
        // Determine the spawning behavior based on the level mode.
        StartCoroutine(GameManager.Instance.Level.LevelMode == ELevelMode.Training
            ? SpawnEmoteInActionArea(waitBeforeSpawn: 0)
            : SpawnEmoteAtSpawnLocation());
    }

    /// <summary>
    /// Spawn a new emote in Training mode when the previous one is failed.
    /// </summary>
    private void OnEmoteFailedCallback(Emoji emoji) => SpawnTrainingEmote();

    /// <summary>
    /// Spawn a new emote in Training mode when the previous one is fulfilled.
    /// </summary>
    private void OnEmoteFulfilledCallback(Emoji emoji, float score) => SpawnTrainingEmote();

    private void SpawnTrainingEmote()
    {
        // In Training mode, spawn a new emote when the previous one is fulfilled.
        if (GameManager.Instance.Level.LevelMode == ELevelMode.Training)
            StartCoroutine(SpawnEmoteInActionArea(waitBeforeSpawn: 1.1f));
    }

    /// <summary>
    /// Coroutine to handle spawning of emotes at the start of the lane.
    /// </summary>
    private IEnumerator SpawnEmoteAtSpawnLocation()
    {
        while (_spawnActive)
        {
            Vector3 position = _spawnLocations[Random.Range(0, _spawnLocations.Count)];
            
            ActivatePooledEmote(position);
            CheckLevelEndConditions();

            yield return new WaitForSeconds(GameManager.Instance.Level.SpawnInterval);
        }
    }

    /// <summary>
    /// Coroutine to handle spawning of emotes in the action area during Training mode.
    /// </summary>
    /// <param name="waitBeforeSpawn">Time to wait before spawning the emote.</param>
    private IEnumerator SpawnEmoteInActionArea(float waitBeforeSpawn)
    {
        yield return new WaitForSeconds(waitBeforeSpawn);
        if (!_spawnActive) 
            yield break;
        ActivatePooledEmote(_actionAreaSpawnLocation);
        CheckLevelEndConditions();
    }
    
    /// <summary>
    /// Activate an emote from the object pool and set its position.
    /// </summary>
    /// <param name="position">The position to spawn the emote at.</param>
    private static void ActivatePooledEmote(Vector3 position)
    {
        // Retrieve an emote object from the pool, set its position, and activate it.
        GameObject emote = _objectPool.GetPooledObject();
        emote.transform.position = position;
        emote.SetActive(true);
    }

    /// <summary>
    /// Check if the end conditions for the level are met, and stop spawning if they are.
    /// </summary>
    private void CheckLevelEndConditions()
    {
        if (GameManager.Instance.CheckLevelEndConditions(GameManager.Instance.LevelProgress.SpawnedEmotesCount))
            StopSpawning();
    }
    
    /// <summary>
    /// Stop spawning emotes when the level stops.
    /// </summary>
    private void OnLevelFinishedCallback() => StopSpawning();
    private void OnLevelStoppedCallback() => StopSpawning();
    
    /// <summary>
    /// Ensure that spawning is stopped when this object is destroyed.
    /// </summary>
    private void OnDestroy() => StopSpawning();

    /// <summary>
    /// Stop the spawning of emotes.
    /// </summary>
    private void StopSpawning() => _spawnActive = false;

}
