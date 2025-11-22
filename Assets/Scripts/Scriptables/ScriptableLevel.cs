using System.Collections.Generic;
using System.IO;
using System.Linq;
using Enums;
using UnityEngine;
using Utilities;
using Random = System.Random;

namespace Scriptables
{ 
    /// <summary>
    /// A ScriptableObject representing a level, containing configurations and utilities for level management.
    /// </summary>
    [CreateAssetMenu(fileName = "New Level")]
    public class ScriptableLevel : ScriptableObject
    {
        // The struct holding all necessary data to configure a level.
        public LevelStruct LevelStruct = new();

        [SerializeField] public List<HighScore> HighScores = new();
        public List<float> EmojiHighScores = new();
        
        // Flag to determine whether to generate a new level file.
        public bool GenerateNewLevelFile = true;
        
        // The file path where the level's JSON representation will be stored.
        private string _filePath;
            
        /// <summary>
        /// Called when the scriptable object is enabled. Used for initialization.
        /// </summary>
        private void OnEnable()
        {
            // Check whether to generate a new level file or load an existing one.
            if (GenerateNewLevelFile)
                GenerateNewLevelSaveFile();
            else
                LoadLevel();
        }

        /// <summary>
        /// Called when the scriptable object is validated. Used to generate a new level file if required.
        /// </summary>
        private void OnValidate()
        {
            if (GenerateNewLevelFile)
                GenerateNewLevelSaveFile();
        }

        /// <summary>
        /// Loads the level data from a JSON file.
        /// </summary>
        private void LoadLevel()
        {
            // Combine directory, subdirectory, and file name to create the complete file path.
            _filePath = Path.Combine(Application.dataPath, "LevelJson", name + ".json");
            
            // Check if the level file exists, log a message and generate a new one if it does not.
            if (!File.Exists(_filePath))
            {
                Debug.Log("File not found: " + _filePath);
                GenerateNewLevelSaveFile();
                return;
            }
                
            // Read the JSON content of the file.
            string json = File.ReadAllText(_filePath);

            LevelStruct levelStruct = JsonUtility.FromJson<LevelStruct>(json);
            
            if (levelStruct.LevelName == "")
                return;
            
            // Deserialize the JSON content to populate the LevelStruct.
            LevelStruct = levelStruct;
        }

        /// <summary>
        /// Generates a new level save file in JSON format.
        /// </summary>
        private void GenerateNewLevelSaveFile()
        {
            // Combine directory, subdirectory, and file name to create the complete file path.
            _filePath = Path.Combine(Application.dataPath, "LevelJson", name + ".json");
            
            // Set the flag to false as we are generating a new level file.
            GenerateNewLevelFile = false;
            
            // If the level mode is predefined, generate a random order for emotes.
            if (LevelStruct.LevelMode == ELevelMode.Predefined)
                LevelStruct.EmoteArray = GenerateRandomOrder(LevelStruct.Emotes.Count);
        
            if (LevelStruct.LevelName == "")
                return;
            
            // Serialize the LevelStruct to JSON and write it to the file.
            File.WriteAllText(_filePath, JsonUtility.ToJson(LevelStruct));
        }

        /// <summary>
        /// Generates a random order of integers.
        /// </summary>
        /// <param name="count">The number of unique integers to generate.</param>
        /// <returns>An array of randomly ordered integers.</returns>
        private int[] GenerateRandomOrder(int count)
        {
            // Initialize a new random number generator.
            Random random = new ();
            
            // Use all emotes if count is zero.
            if (count == 0)
                count = 7;

            // Create a list of integers from 0 to (count-1), each repeated a specific number of times.
            IEnumerable<int> repeatedNumbers = Enumerable.Range(0, count).SelectMany(i => Enumerable.Repeat(i, LevelStruct.EmoteRepeatAmount));
        
            // Shuffle the list to get a random order and convert it to an array.
            int[] randomNumbers = repeatedNumbers.OrderBy(_ => random.Next()).ToArray();

            return randomNumbers;
        }

        public void AddHighScore(HighScore highScore)
        {
            HighScores.Add(highScore);
            EmojiHighScores.Clear();
            foreach (HighScore score in HighScores)
            {
                EmojiHighScores.Add((float)score.FulfilledEmotes / score.TotalEmotes * 100);
            }
            EmojiHighScores.Sort();
        }
    }
}