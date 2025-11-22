using System.Collections.Generic;
using System.Linq;
using Scriptables;
using UnityEngine;
using Utilities;

namespace Manager
{
    public class HighScoreManage : MonoBehaviour
    {
        public void OnEnable()
        {
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
        }

        private void OnDestroy()
        {
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
        }

        private void OnLevelFinishedCallback()
        {
            List<ScriptableLevel> levels =  Resources.LoadAll<ScriptableLevel>("Levels").ToList();

            HighScore highScore = new()
            {
                FulfilledEmotes = GameManager.Instance.LevelProgress.FulfilledEmoteCount,
                TotalEmotes = GameManager.Instance.LevelProgress.SpawnedEmotesCount,
                LevelScore = GameManager.Instance.LevelProgress.LevelScore,
                UserID = EditorUI.EditorUI.Instance.UserID
            };
            
            levels.FirstOrDefault(l => l.name == GameManager.Instance.Level.LevelName)?.AddHighScore(highScore);
            
        }
    }
}