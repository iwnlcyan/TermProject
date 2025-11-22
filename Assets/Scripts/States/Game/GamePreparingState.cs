using System;
using Enums;
using Manager;
using Scriptables;
using Systems;
using UnityEngine;

namespace States.Game
{
    /// <summary>
    /// Represents the state of the game while it is preparing/idle.
    /// </summary>
    public class GamePreparingState : GameState
    {
        /// <summary>
        /// Enter the preparing state, setting the time scale to normal and invoking the LevelStopped event.
        /// </summary>
        public override void EnterState()
        {
            GameManager.Instance.RestartTimeScale();
            EventManager.InvokeLevelStopped();
        }

        /// <summary>
        /// Leave the preparing state. This method is intentionally left empty as there is no cleanup needed.
        /// </summary>
        public override void LeaveState()
        {
        }

        /// <summary>
        /// Handle user interface input specific to the preparing state.
        /// </summary>
        /// <param name="uiType">The type of UI interaction.</param>
        /// <exception cref="ArgumentOutOfRangeException">Thrown when an unexpected UIType is received.</exception>
        public override void HandleUIInput(UIType uiType)
        {
            switch (uiType)
            {
                case UIType.StartLevel:
                case UIType.StartStopLevel:
                    if (LoggingSystem.Instance.FinishedSaving())
                        GameManager.Instance.SwitchState(GameManager.Instance.PlayingLevelState);
                    else
                        Debug.Log("Still writing images");
                    break;
                case UIType.StopLevel:
                case UIType.PauseLevel:
                case UIType.ContinueEndScreen:
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
            GameManager.Instance.SetNewLevel(level);
        }
    }
}