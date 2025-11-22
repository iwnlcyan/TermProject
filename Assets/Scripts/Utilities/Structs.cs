using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Data;
using Enums;
using UnityEngine;

namespace Utilities
{
    /// <summary>
    /// Represents the probabilities of the emotions.
    /// </summary>
    [SuppressMessage("ReSharper", "InconsistentNaming")]
    public struct Probabilities
    {
        public float anger;
        public float disgust;
        public float fear;
        public float happiness;
        public float neutral;
        public float sadness;
        public float surprise;
    }

    /// <summary>
    /// Represents the settings and data for a game level.
    /// </summary>
    [Serializable]
    public struct LevelStruct
    {
        /// <summary>
        /// Gets or sets the name of the level.
        /// </summary>
        public string LevelName;

        /// <summary>
        /// Gets or sets the game mode of the level.
        /// </summary>
        public ELevelMode LevelMode;

        /// <summary>
        /// Gets or sets the movement speed in the level.
        /// </summary>
        public float MovementSpeed;

        /// <summary>
        /// Gets or sets the interval between spawns in the level.
        /// </summary>
        public float SpawnInterval;

        /// <summary>
        /// Gets or sets the count of Emojis in the level.
        /// </summary>
        [Tooltip("Acts as timer in Training mode")]
        public int Count;

        /// <summary>
        /// Gets or sets the predefined emotes for the level.
        /// </summary>
        [Header("Predefined Level Settings")]
        public List<EEmote> Emotes;

        /// <summary>
        /// Gets or sets the amount to repeat each emote in the level.
        /// </summary>
        public int EmoteRepeatAmount;

        /// <summary>
        /// Gets or sets the array of emote IDs for the level.
        /// </summary>
        public int[] EmoteArray;
    }

    public struct Emoji
    {
        public EEmote Emote;

        public int EmoteID;

        public int Texture;
    }

    [Serializable]
    public struct HighScore
    {
        /// <summary>Gets the count of fulfilled emotes.</summary>
        public int FulfilledEmotes { get; internal set; }

        /// <summary>Gets the count of spawned emotes.</summary>
        public int TotalEmotes { get; internal set; }
        
        /// <summary>Gets the current level score.</summary>
        public int LevelScore { get; internal set; }

        public string UserID { get; internal set; }
    }
}