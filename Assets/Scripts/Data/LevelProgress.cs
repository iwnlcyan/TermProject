using System.Collections.Generic;
using System.Linq;
using Utilities;

namespace Data
{
    public class LevelProgress
    {
        /// <summary>Gets the count of fulfilled emotes.</summary>
        public int FulfilledEmoteCount { get; internal set; }
        
        /// <summary>Gets the count of finished emotes.</summary>
        public int FinishedEmoteCount { get; internal set; }

        /// <summary>List of spawned emotes.</summary>
        internal readonly List<Emoji> SpawnedEmotes = new();

        /// <summary>Gets the count of spawned emotes.</summary>
        public int SpawnedEmotesCount => SpawnedEmotes.Count;
        
        /// <summary>Gets the current level score.</summary>
        public int LevelScore { get; internal set; }

        /// <summary>Gets the list of emotes currently in the action area.</summary>
        private readonly List<Emoji> _emojiInActionArea = new();
    

        ///<summary>
        /// Indicates whether any emotes are in the action area.
        /// </summary>
        public bool EmojisAreInActionArea => _emojiInActionArea.Any();
        
        /// <summary>
        /// Gets the first emote in the action area or the default value.
        /// </summary>
        public Emoji GetEmojiInActionArea => _emojiInActionArea.LastOrDefault();
        
        /// <summary>
        /// Adds an emote to the action area.
        /// </summary>
        public void AddEmoteToActionArea(Emoji emoji) => _emojiInActionArea.Add(emoji);

        /// <summary>
        /// Removes an emote from the action area.
        /// </summary>
        public bool RemoveEmoteFromActionArea(Emoji emoji) => _emojiInActionArea.Remove(emoji);

        public void ClearEmotesInActionAreaList() => _emojiInActionArea.Clear();
    }
}