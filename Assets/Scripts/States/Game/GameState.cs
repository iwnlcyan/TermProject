using Enums;
using Scriptables;

namespace States.Game
{
    /// <summary>
    /// Represents the base class for all game states, providing abstract methods to enter and leave the state, and to handle UI inputs.
    /// </summary>
    public abstract class GameState
    {
        /// <summary>
        /// Called when the game enters this state.
        /// </summary>
        public abstract void EnterState();

        /// <summary>
        /// Called when the game leaves this state.
        /// </summary>
        /// 
        public abstract void LeaveState();

        /// <summary>
        /// Handles UI input of type <see cref="UIType"/>.
        /// </summary>
        /// <param name="uiType">The type of UI input to handle.</param>
        public abstract void HandleUIInput(UIType uiType);

        /// <summary>
        /// Handles UI input of type <see cref="ScriptableLevel"/>.
        /// </summary>
        /// <param name="level">The scriptable level to handle.</param>
        public abstract void HandleUIInput(ScriptableLevel level);
    }
}