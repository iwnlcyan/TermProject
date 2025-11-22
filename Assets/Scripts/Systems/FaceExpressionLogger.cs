using System;
using System.Collections;
using Data;
using Manager;
using UnityEngine;

namespace Systems
{
    public class FaceExpressionLogger : MonoBehaviour
    {
        private FaceExpressionHandler _faceExpressionHandler;
        [SerializeField] private int TargetFPS = 0;
        private Coroutine _coroutine;

        private void Start()
        {
            _faceExpressionHandler = new FaceExpressionHandler();
        }

        private void OnEnable()
        {
            EventManager.OnLevelStarted += OnLevelStartedCallback;
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
        }

        private void OnDestroy()
        {
            EventManager.OnLevelStarted -= OnLevelStartedCallback;
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
        }

        private void OnLevelStartedCallback()
        {
            if (LoggingSystem.Instance.LogFaceExpressions)
                _coroutine = StartCoroutine(LogFaceExpression());
        }

        private void OnLevelFinishedCallback()
        {
            if (_coroutine != null)
                StopCoroutine(_coroutine);
            _coroutine = null;
        }

        private IEnumerator LogFaceExpression()
        {
            
            // Interval between each snapshot.
            float interval = 0;
            if (TargetFPS > 0)
                interval = 1f / TargetFPS;
            float nextPostTime = Time.realtimeSinceStartup + interval;
            
            while (GameManager.Instance.IsPlayingLevel)
            {
                while (!WebcamManager.EmojiIsInWebcamArea)
                {
                    nextPostTime = Time.realtimeSinceStartup + interval;
                    yield return null;
                }

                FaceExpression faceExpression = new()
                {
                    Timestamp = LoggingSystem.GetUnixTimestamp(),
                    LevelID = GameManager.Instance.Level.LevelName,
                    Emoji = WebcamManager.EmojiInWebcamArea,
                    FaceExpressionJson = _faceExpressionHandler.GetFaceExpressionsAsJson()
                };

                LoggingSystem.Instance.AddToFaceExpressionList(faceExpression);
                
                // Calculate time needed to wait to ensure periodic execution
                float waitTime = Math.Max(nextPostTime - Time.realtimeSinceStartup, 0);
                
                // Wait at least a single frame, if the waitTime is 0
                if (waitTime > 0)
                    yield return new WaitForSecondsRealtime(waitTime);
                else
                    yield return null;

                // iterate timer to next interval
                nextPostTime += interval;
            }
        }
    }
}