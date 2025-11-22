using Enums;
using Manager;
using UnityEngine;
using Utilities;

namespace States.Emojis
{
    /// <summary>
    /// Represents the state of an Emoji when it leaved the ActionArea.
    /// </summary>
    public class EmojiLeavingState : EmojiState
    {
        /// <summary>
        /// Method called when the Emoji enters this state.
        /// Initiates the fading out and deactivation process of the Emoji.
        /// </summary>
        /// <param name="emojiManager">The manager controlling the Emoji.</param>
        public override void EnterState(EmojiManager emojiManager)
        {
            // Start the fade-out and deactivation process of the Emoji.
            emojiManager.FadeOut();
        }

        public override void Update(EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }

        public override void OnTriggerEnter(Collider collider, EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }

        public override void OnTriggerExit(Collider collider, EmojiManager emojiManager)
        {
            if (collider.CompareTag("WebcamArea"))
                EventManager.InvokeEmoteExitedWebcamArea(emojiManager.Emoji);
        }

        public override void OnEmotionDetectedCallback(EmojiManager emojiManager, EEmote emote)
        {
            // Implementation not required for this state.
        }

        public override void Despawn(EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }
    }
}