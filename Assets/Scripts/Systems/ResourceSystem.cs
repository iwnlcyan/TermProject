using System.Collections.Generic;
using System.Linq;
using Enums;
using Scriptables;
using UnityEngine;

namespace Systems
{
    /// <summary>
    /// Manages and provides access to game resources emojis.
    /// </summary>
    public class ResourceSystem
    {
        /// <summary>
        /// Initializes the ResourceSystem instance and assembles resources for emojis.
        /// </summary>
        public ResourceSystem()
        {
            AssembleEmojiScriptables();
        }

        /// <summary>
        /// Gets a dictionary of emoji textures indexed by their emote type.
        /// </summary>
        public static Dictionary<EEmote, ScriptableEmoji> EmojiScriptables { get; private set; }
    
        /// <summary>
        /// Loads all ScriptableEmoji assets from the "Emojis" resources folder, and stores them in a list and a dictionary for quick access.
        /// </summary>
        private static void AssembleEmojiScriptables()
        {
            EmojiScriptables = Resources.LoadAll<ScriptableEmoji>("Emojis")
                .ToDictionary(emoji => emoji.EEmote, emoji => emoji);
        }
    }
}
