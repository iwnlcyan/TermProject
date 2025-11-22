using System;
using Enums;
using Manager;
using Scriptables;
using UnityEngine;

namespace States.Game
{
    /// <summary>
    /// Represents the state of the game when a level has finished, handling the transition and user interactions during this period.
    /// </summary>
    public class GameLevelFinishedState : GameState
    {
        /// <summary>
        /// Actions to perform when entering the level finished state.
        /// </summary>
        public override void EnterState()
        {
            // Notify other parts of the game that the level has finished.
            EventManager.InvokeLevelFinished();
            
            // Pause the game's time scale, effectively pausing the game.
            GameManager.Instance.StopTimeScale();
        }

        public override void LeaveState()
        {
        }

        /// <summary>
        /// Handle user interface input specific to the finished state.
        /// </summary>
        /// <param name="uiType">The type of UI interaction.</param>
        /// <exception cref="ArgumentOutOfRangeException">Thrown when an unexpected UIType is received.</exception>
        public override void HandleUIInput(UIType uiType)
        {
            switch (uiType)
            {
                case UIType.ContinueEndScreen:
                case UIType.StartStopLevel:
                    GameManager.Instance.SwitchState(GameManager.Instance.PreparingState);
                    break;
                case UIType.StartLevel:
                case UIType.StopLevel:
                case UIType.PauseLevel:
                case UIType.Default:
                default:
                    throw new ArgumentOutOfRangeException(nameof(uiType), uiType, null);
            }
        }

        /// <summary>
        /// Handle a new level selection.
        /// </summary>
        /// <param name="level">The ScriptableLevel representing the new level.</param>
        public override void HandleUIInput(ScriptableLevel level)
        {
            Debug.LogWarning("Level input is not expected during the playing state.");
        }
    }
}