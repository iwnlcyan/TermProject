using System;
using System.Collections.Generic;
using System.Linq;
using Data;
using Enums;
using Manager;
using Systems;
using UnityEngine;
using Utilities;
using Random = UnityEngine.Random;

namespace States.Emojis
{
    /// <summary>
    /// Represents the initial state of an Emoji when it is first spawned in the game.
    /// </summary>
    public class EmojiPreState : EmojiState
    {
        /// <summary>
        /// Method called when the Emoji enters this state.
        /// </summary>
        /// <param name="emojiManager">The manager controlling the Emoji.</param>
        public override void EnterState(EmojiManager emojiManager)
        {
            // Set the Emoji's Rigidbody to be kinematic and reset its rotation.
            emojiManager.Rigidbody.isKinematic = true;
            emojiManager.transform.rotation = Quaternion.identity;

            // Determine and set the current Emoji's emotion.
            GetEmote(emojiManager);
            
            GameManager.Instance.IncreaseSpawnedEmotesCount(emojiManager.Emoji);

            // Set the Emoji's title text based on its emotion.
            SetEmojiName(emojiManager);

            // Initialize the Emoji's visual elements.
            SetEmojiTextures(emojiManager);
        }

        /// <summary>
        /// Determines and sets the current Emoji's emotion.
        /// </summary>
        /// <param name="emojiManager">The manager of the Emoji.</param>
        private static void GetEmote(EmojiManager emojiManager)
        {
            LevelStruct level = GameManager.Instance.Level;
            LevelProgress levelProgress = GameManager.Instance.LevelProgress;

            int emoteIndex = level.EmoteArray.Length > 0
                // Get the next emotion from the predefined list, based on already spawned emojis.
                ? level.EmoteArray[levelProgress.SpawnedEmotesCount % level.EmoteArray.Length]
                // get random Emote if no predefined list exists. -2 to compensate default enum.
                : Random.Range(0, Enum.GetValues(typeof(EEmote)).Length - 2);

            EEmote emote = level.Emotes.Any()
                ? level.Emotes[emoteIndex % level.Emotes.Count]
                : (EEmote)(emoteIndex + 1);
            
            emojiManager.Emoji = new Emoji
            {
                // If a custom Emote list is set, use it. Otherwise, use the EEmote enum. + 1 to compensate default enum.
                Emote = emote,
                EmoteID = levelProgress.SpawnedEmotesCount,
                Texture = levelProgress.SpawnedEmotes.Count(e => e.Emote == emote)
            };
        }

        public override void Update(EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }

        /// <summary>
        /// Trigger enter event handler. Switches the Emoji to the IntraState when triggered.
        /// </summary>
        public override void OnTriggerEnter(Collider collider, EmojiManager emojiManager)
        {
            if (collider.CompareTag("ActionArea"))
                emojiManager.SwitchState(emojiManager.IntraState);
            else if (collider.CompareTag("WebcamArea"))
                EventManager.InvokeEmoteEnteredWebcamArea(emojiManager.Emoji);
        }

        /// <summary>
        /// Trigger exit event handler. Not used in this state.
        /// </summary>
        public override void OnTriggerExit(Collider collider, EmojiManager emojiManager)
        {
            // Implementation not required for this state.
        }

        /// <summary>
        /// Emotion detected event handler. Not used in this state.
        /// </summary>
        public override void OnEmotionDetectedCallback(EmojiManager emojiManager, EEmote emote)
        {
            // Implementation not required for this state.
        }

        public override void Despawn(EmojiManager emojiManager)
        {
            emojiManager.SwitchState(emojiManager.LeavingState);
        }

        /// <summary>
        /// Initializes the Emoji's visual elements based on its emotion.
        /// </summary>
        /// <param name="emojiManager">The manager of the Emoji.</param>
        private static void SetEmojiTextures(EmojiManager emojiManager)
        {
            // Get the texture for the current Emoji's emotion.
            //Texture texture = ResourceSystem.EmojiTextures[emojiManager.Emoji.Emote];
            
            List<Texture> textures = ResourceSystem.EmojiScriptables[emojiManager.Emoji.Emote].Textures;

            Texture texture = textures[emojiManager.Emoji.Texture % textures.Count];

            // Set the Emoji's material properties.
            emojiManager.EmojiMaterial.SetTexture(emojiManager.Sprite, texture);
            emojiManager.EmojiMaterial.SetFloat(emojiManager.FailedColorAmount, 0);
            emojiManager.EmojiMaterial.SetFloat(emojiManager.SuccessColorAmount, 0);
            emojiManager.EmojiMaterial.SetFloat(emojiManager.DissolveAmount, 0);
        }

        private static void SetEmojiName(EmojiManager emojiManager)
        {
            string name = GameManager.Instance.UseGermanEmoteNames 
                ? ResourceSystem.EmojiScriptables[emojiManager.Emoji.Emote].GermanName 
                : ResourceSystem.EmojiScriptables[emojiManager.Emoji.Emote].EnglishName;
            
            emojiManager.EmoteTitle.text = name;
        }
    }
}