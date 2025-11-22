using Enums;
using Manager;
using UnityEngine;
using Utilities;

namespace States.Emojis
{
    /// <summary>
    /// Represents a base state for the EmojiManager's state machine.
    /// </summary>
    public abstract class EmojiState
    {
        /// <summary>
        /// Invoked when the emoji enters this state.
        /// </summary>
        /// <param name="emojiManager">The emoji manager instance.</param>
        public abstract void EnterState(EmojiManager emojiManager);

        /// <summary>
        /// Invoked every frame when the emoji is in this state.
        /// </summary>
        /// <param name="emojiManager">The emoji manager instance.</param>
        public abstract void Update(EmojiManager emojiManager);

        /// <summary>
        /// Invoked when the emoji enters a collider.
        /// </summary>
        /// <param name="collider"></param>
        /// <param name="emojiManager">The emoji manager instance.</param>
        public abstract void OnTriggerEnter(Collider collider, EmojiManager emojiManager);

        /// <summary>
        /// Invoked when the emoji leaves a collider.
        /// </summary>
        /// <param name="collider"></param>
        /// <param name="emojiManager">The emoji manager instance.</param>
        public abstract void OnTriggerExit(Collider collider, EmojiManager emojiManager);

        /// <summary>
        /// Invoked when an emotion is detected by the FER.
        /// </summary>
        /// <param name="emojiManager">The emoji manager instance.</param>
        /// <param name="emote">The detected emotion.</param>
        public abstract void OnEmotionDetectedCallback(EmojiManager emojiManager, EEmote emote);

        public abstract void Despawn(EmojiManager emojiManager);
    }
}

