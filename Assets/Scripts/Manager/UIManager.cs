using System;
using System.Collections;
using System.Collections.Generic;
using Data;
using Enums;
using Systems;
using TMPro;
using UnityEngine;
using Utilities;

namespace Manager
{
    /// <summary>
    /// Manages the User Interface (UI) elements and interactions within the game.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        [Header("UI GameObjects")]
        [SerializeField] private GameObject PreparingUI;
        [SerializeField] private GameObject LevelPlayingUI;
        [SerializeField] private GameObject LevelEndScreenUI;
        

        [Header("Score UI")]
        [SerializeField] private List<TMP_Text> LevelNameField;
        [SerializeField] private TMP_Text ProgressField;
        [SerializeField] private List<TMP_Text> ResultField;
        [SerializeField] private List<TMP_Text> ScoreField;
        [SerializeField] private TMP_Text DetailedEmojiScoreField;
        [SerializeField] private TMP_Text DetailedTimeScoreField;
        
        // Holds the data for the current level.
        private LevelStruct _level;
        
        private int _maxScore;

        private void Awake()
        {
            EventManager.OnLevelStarted += OnLevelStartedCallback;
            EventManager.OnLevelStopped += OnLevelStoppedCallback;
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
            EventManager.OnEmoteExitedActionArea += EmoteExitedActionAreaCallback;
            EventManager.OnEmoteFulfilled += OnEmoteFulfilledCallback;

            // Load the UI elements for level selection.
            ResetScoreUI();
            // Initialize the UI state.
            OnLevelStoppedCallback();
        }

        private void OnDisable()
        {
            EventManager.OnLevelStarted -= OnLevelStartedCallback;
            EventManager.OnLevelStopped -= OnLevelStoppedCallback;
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
            EventManager.OnEmoteExitedActionArea -= EmoteExitedActionAreaCallback;
            EventManager.OnEmoteFulfilled -= OnEmoteFulfilledCallback;
        }

        private void Update()
        {
            if (GameManager.Instance.IsPlayingLevel)
                return;
            ProgressField.text = $"{LoggingSystem.Instance.SnapshotCount}";
        }


        /// <summary>
        /// Updates the score UI when an emote exits the action area.
        /// </summary>
        private void EmoteExitedActionAreaCallback(Emoji emoji) => StartCoroutine(UpdateScoreUI());
        
        /// <summary>
        /// Updates the score UI when an emote is fulfilled.
        /// </summary>
        private void OnEmoteFulfilledCallback(Emoji emoji, float score) => StartCoroutine(UpdateScoreUI());

        /// <summary>
        /// Loads the UI for the end screen, displaying level name and score.
        /// </summary>
        private void LoadEndScreenUI() => StartCoroutine(UpdateScoreUI());

        /// <summary>
        /// Loads the score UI with the current game progress and score.
        /// </summary>
        private void LoadScoreUI()
        {
            foreach (TMP_Text t in LevelNameField)
            {
                t.text = _level.LevelName;
            }

            StartCoroutine(UpdateScoreUI());
        }

        /// <summary>
        /// Updates the score UI based on the current game progress and score.
        /// </summary>
        private IEnumerator UpdateScoreUI()
        {
            // Wait to the end of the frame to ensure LevelProgress has been properly updated
            yield return new WaitForEndOfFrame();
            
            LevelProgress levelProgress = GameManager.Instance.LevelProgress;

            ProgressField.text = _level.LevelMode switch
            {
                ELevelMode.Training => "",
                ELevelMode.Predefined => $"{Math.Round((float)levelProgress.FinishedEmoteCount / _level.EmoteArray.Length * 100)}%",
                _ => $"{Math.Round((float)levelProgress.FinishedEmoteCount / _level.Count * 100)}%"
            };

            foreach (TMP_Text t in ResultField)
            {
                t.text = _level.LevelMode switch
                {
                    ELevelMode.Training => $"{levelProgress.FulfilledEmoteCount} / {GameManager.Instance.LevelProgress.SpawnedEmotesCount}",
                    ELevelMode.Predefined => $"{levelProgress.FulfilledEmoteCount} / {_level.EmoteArray.Length} ({Math.Round((float)levelProgress.FulfilledEmoteCount / _level.EmoteArray.Length * 100 , 1)}%)",
                    _ => $"{levelProgress.FulfilledEmoteCount} / {_level.Count} ({Math.Round((float)levelProgress.FulfilledEmoteCount / _level.EmoteArray.Length * 100 , 1)}%)"
                };
            }

            foreach (TMP_Text t in ScoreField)
            {
                string maxScoreText = "";
                if (_maxScore > 0)
                    maxScoreText = $" / {_maxScore}";
                t.text = $"{levelProgress.LevelScore}{maxScoreText}";
            }

            DetailedEmojiScoreField.text = $"Matched Emojis: {levelProgress.FulfilledEmoteCount}";
            DetailedTimeScoreField.text = $"Time Bonus: {Math.Round((float)(levelProgress.LevelScore - levelProgress.FulfilledEmoteCount * GameManager.BaseScoreForCompletion) / GameManager.ScoreMultiplier / 10, 1)}";
        }

        /// <summary>
        /// Resets the score UI.
        /// </summary>
        private void ResetScoreUI()
        {
            ProgressField.text = "";
            
            foreach (TMP_Text t in LevelNameField)
            {
                t.text = "";
            }

            foreach (TMP_Text t in ResultField)
            {
                t.text = "";
            }

            foreach (TMP_Text t in ScoreField)
            {
                t.text = "";
            }
        }

        /// <summary>
        /// Updates the UI to reflect the level started state.
        /// </summary>
        private void OnLevelStartedCallback()
        {
            _level = GameManager.Instance.Level;

            _maxScore = GameManager.Instance.GetMaxScore();

            PreparingUI.SetActive(false);
            LevelPlayingUI.SetActive(true);
            LevelEndScreenUI.SetActive(false);
            
            LoadScoreUI();
        }

        /// <summary>
        /// Updates the UI to reflect the level stopped state.
        /// </summary>
        private void OnLevelStoppedCallback()
        {
            ResetScoreUI();
            LevelPlayingUI.SetActive(false);
            PreparingUI.SetActive(true);
            LevelEndScreenUI.SetActive(false);
        }
        
        /// <summary>
        /// Updates the UI to reflect the level finished state.
        /// </summary>
        private void OnLevelFinishedCallback()
        {
            LevelPlayingUI.SetActive(false);
            PreparingUI.SetActive(false);
            LevelEndScreenUI.SetActive(true);
            LoadEndScreenUI();
        }

        // Methods to handle button presses, triggering corresponding actions in the GameManager.
        public void OnStartButtonPressed() => GameManager.Instance.OnButtonPressed(UIType.StartLevel);
        public void OnPauseButtonPressed() => GameManager.Instance.OnButtonPressed(UIType.PauseLevel);
        public void OnStopButtonPressed() => GameManager.Instance.OnButtonPressed(UIType.StopLevel);
        public void OnEndScreenButtonPressed() => GameManager.Instance.OnButtonPressed(UIType.ContinueEndScreen);
    }
}