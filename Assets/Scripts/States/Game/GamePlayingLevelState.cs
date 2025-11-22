using System;
using Data;
using Enums;
using Manager;
using Scriptables;
using UnityEngine;
using Utilities;

namespace States.Game
{
    /// <summary>
    /// Represents the state of the game when a level is actively being played.
    /// </summary>
    public class GamePlayingLevelState : GameState
    {

        public LevelProgress LevelProgress;
        public int MaxScore { get; private set; }

        public override void EnterState()
        {
            LevelProgress = new LevelProgress();

            CalculateMaxScore();
            
            EventManager.OnEmoteEnteredActionArea += EmoteEnteredActionAreaCallback;
            EventManager.OnEmoteExitedActionArea += EmoteExitedActionAreaCallback;
            EventManager.OnEmoteFulfilled += OnEmoteFulfilledCallback;
            
            // Notify the game that a new level has started.
            EventManager.InvokeLevelStarted();
        }

        private void CalculateMaxScore()
        {
            
            int emojiCount = 0;
            switch (GameManager.Instance.Level.LevelMode)
            {
                case ELevelMode.Predefined:
                    emojiCount = GameManager.Instance.Level.EmoteArray.Length;
                    break;
                case ELevelMode.Count:
                    emojiCount = GameManager.Instance.Level.Count;
                    break;
                case ELevelMode.Training:
                    break;
                default:
                    throw new ArgumentOutOfRangeException();
            }

            MaxScore =  emojiCount * (GameManager.BaseScoreForCompletion +
                                      (int)(GameManager.Instance.ActionAreaSize * 0.9 / GameManager.Instance.Level.MovementSpeed * GameManager.ScoreMultiplier) * 10);
        }


        public override void LeaveState()
        {
            LevelProgress.ClearEmotesInActionAreaList();
            
            EventManager.OnEmoteEnteredActionArea -= EmoteEnteredActionAreaCallback;
            EventManager.OnEmoteExitedActionArea -= EmoteExitedActionAreaCallback;
            EventManager.OnEmoteFulfilled -= OnEmoteFulfilledCallback;
        }

        /// <summary>
        /// Handles the behavior when an emote enters the action area.
        /// </summary>
        /// <param name="emoji">The emote that entered.</param>
        private void EmoteEnteredActionAreaCallback(Emoji emoji) => LevelProgress.AddEmoteToActionArea(emoji);

        /// <summary>
        /// Handles the behavior when an emote exits the action area.
        /// </summary>
        /// <param name="emoji">The emote that exited.</param>
        private void EmoteExitedActionAreaCallback(Emoji emoji)
        {
            if (!LevelProgress.RemoveEmoteFromActionArea(emoji))
                Debug.LogWarning($"Attempted to remove an emote that wasn't in the action area: {emoji}");
            
            LevelProgress.FinishedEmoteCount++;
            if (GameManager.Instance.CheckLevelEndConditions(LevelProgress.FinishedEmoteCount))
                GameManager.Instance.SwitchState(GameManager.Instance.LevelFinishedState);
        }

        /// <summary>
        /// Calculates and updates the level score when an emote is fulfilled.
        /// The score is calculated based on the base score for completion and a multiplier based on the time left.
        /// </summary>
        /// <param name="emoji">The emote that was fulfilled.</param>
        /// <param name="score">The base score associated with the emote.</param>
        private void OnEmoteFulfilledCallback(Emoji emoji, float score)
        {
            LevelProgress.FulfilledEmoteCount++;
            LevelProgress.LevelScore += GameManager.BaseScoreForCompletion + (int)(score * GameManager.ScoreMultiplier) * 10;
        }

        /// <summary>
        /// Handle user interface input specific to the playing state.
        /// </summary>
        /// <param name="uiType">The type of UI interaction.</param>
        /// <exception cref="ArgumentOutOfRangeException">Thrown when an unexpected UIType is received.</exception>
        public override void HandleUIInput(UIType uiType)
        {
            switch (uiType)
            {
                case UIType.StopLevel:
                case UIType.StartStopLevel:
                    // Transition to the preparing state when the level is stopped.
                    GameManager.Instance.SwitchState(GameManager.Instance.LevelFinishedState);
                    break;
                case UIType.PauseLevel:
                case UIType.StartLevel:
                case UIType.Default:
                case UIType.ContinueEndScreen:
                default:
                    throw new ArgumentOutOfRangeException(nameof(uiType), uiType, null);
            }
        }

        /// <summary>
        /// Handles level-specific UI inputs. These are unexpected during the playing state.
        /// </summary>
        /// <param name="level">The level associated with the UI input.</param>
        public override void HandleUIInput(ScriptableLevel level)
        {
            Debug.LogWarning("Level input is not expected during the playing state.");
        }

        /// <summary>
        /// Increments the count of spawned emotes.
        /// </summary>
        /// <param name="emoji"></param>
        public void IncreaseSpawnedEmotesCount(Emoji emoji) => LevelProgress.SpawnedEmotes.Add(emoji);
    }
}