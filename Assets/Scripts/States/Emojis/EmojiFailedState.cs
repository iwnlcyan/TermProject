using Enums;
using Manager;
using UnityEngine;
using Utilities;

namespace States.Emojis
{
    /// <summary>
    /// Represents the state of an Emoji when the player has failed to match the emotion.
    /// </summary>
    public class EmojiFailedState : EmojiState
    {
        /// <summary>
        /// Called when the Emoji enters the Failed State.
        /// Sets the visual feedback, triggers relevant events, and transitions to the Leaving State.
        /// </summary>
        /// <param name="emojiManager">The manager controlling the Emoji.</param>
        public override void EnterState(EmojiManager emojiManager)
        {
            // Set the material property to give visual feedback of failure.
            emojiManager.EmojiMaterial.SetFloat(emojiManager.FailedColorAmount, 0.5f);
            
            // Notify other systems that the Emoji has exited the Action Area.
            EventManager.InvokeEmoteExitedActionArea(emojiManager.Emoji);
            
            // Notify other systems that the Emoji has failed to be matched.
            EventManager.InvokeEmoteFailed(emojiManager.Emoji);
            
            // Play the failure animation.
            emojiManager.EmojiAnimator.Play("EmojiFail");
            
            // Switch to the Leaving State.
            emojiManager.SwitchState(emojiManager.LeavingState);
        }

        public override void Update(EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }

        public override void OnTriggerEnter(Collider collider, EmojiManager emojiManager)
        {
            Debug.Log("NotImplementedException");
        }

        public override void OnTriggerExit(Collider collider, EmojiManager emojiManager)
        {
            Debug.Log("NotImplementedException");
        }

        public override void OnEmotionDetectedCallback(EmojiManager emojiManager, EEmote emote)
        {
            // Implementation not required for this state.
        }

        public override void Despawn(EmojiManager emojiManager)
        {
            emojiManager.SwitchState(emojiManager.LeavingState);
        }
    }
}
