using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Data;
using Enums;
using Systems;
using UnityEngine;
using UnityEngine.Profiling;
using Utilities;

namespace Manager
{
    /// <summary>
    /// Manages the webcams, captures and processes images.
    /// </summary>
    public class WebcamManager : MonoBehaviour
    {
        // List to store references to the active webcams.
        private static readonly List<WebCamTexture> Webcams = new();
        
        // List of RenderTextures that are set up to display the webcam feeds.
        [SerializeField] private List<RenderTexture> RenderTextures = new();

        // Desired width and height for the webcam capture.
        [SerializeField] private int RequestedCameraWidth = 1280;
        [SerializeField] private int RequestedCameraHeight = 720;
        
        // The target frames per second for taking snapshots from the webcam.
        [SerializeField] private int TargetSnapshotFPS = 30;

        // A list that tracks which emotes are currently in the webcam area.
        private static readonly List<Emoji> EmojisInWebcamArea = new();

        // A texture for processing the webcam image.
        private static Texture2D _texture;
        
        // Accessors for webcam width and height.
        public static int WebcamWidth => Webcams[0].width;
        public static int WebcamHeight => Webcams[0].height;
        public static Emoji EmojiInWebcamArea => EmojisInWebcamArea.FirstOrDefault();
        public static bool EmojiIsInWebcamArea => EmojisInWebcamArea.Any();


        // A reference to the coroutine that takes continuous snapshots.
        private Coroutine _coroutine;

        private void Start()
        {
            // Get webcam names from the EditorUI
            string mainWebcamName = EditorUI.EditorUI.Instance.GetMainWebcam();
            string secondaryWebcamName = EditorUI.EditorUI.Instance.GetSecondaryWebcam();
            
            // Set up the webcams and create a texture for image processing.
            InitializeWebcams(mainWebcamName, secondaryWebcamName);
            _texture = new Texture2D(Webcams[0].width, Webcams[0].height);
            
            EventManager.OnEmoteEnteredWebcamArea += EmoteEnteredWebcamAreaCallback;
            EventManager.OnEmoteExitedWebcamArea += EmoteExitedWebcamAreaCallback;
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
        }

        private void OnDestroy()
        {
            // Clean up webcams and textures, and unsubscribe from events on destruction.
            foreach (WebCamTexture webcam in Webcams) 
                webcam.Stop();
        
            foreach (RenderTexture texture in RenderTextures) 
                texture.Release();
            
            EventManager.OnEmoteEnteredWebcamArea -= EmoteEnteredWebcamAreaCallback;
            EventManager.OnEmoteExitedWebcamArea -= EmoteExitedWebcamAreaCallback;
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
        }

        private void OnLevelFinishedCallback()
        {
            EmojisInWebcamArea.Clear();

            StopCoroutine();

            EditorUIFerStats.Instance.SnapshotFPS = $"0 ({EditorUIFerStats.Instance.SnapshotFPS})";
        }

        private void StopCoroutine()
        {
            if (_coroutine == null)
                return;
            StopCoroutine(_coroutine);
            _coroutine = null;
        }

        private void EmoteEnteredWebcamAreaCallback(Emoji emoji)
        {      
            if (!GameManager.Instance.IsPlayingLevel)
                return;
            // Add the emote to the tracking list and start the snapshot coroutine if not already running.
            EmojisInWebcamArea.Add(emoji);
            _coroutine ??= StartCoroutine(TakeSnapshotCoroutine());
        }

        private void EmoteExitedWebcamAreaCallback(Emoji emoji)
        {
            if (!GameManager.Instance.IsPlayingLevel)
                return;
            // Remove the emote from the tracking list.
            EmojisInWebcamArea.Remove(emoji);
        }

        private void Update()
        {
            // On each frame, update the RenderTextures with the latest webcam image if it has updated.
            for (int i = 0; i < Webcams.Count; i++)
                if (Webcams[i].didUpdateThisFrame)
                    Blit(i);
        }

        /// <summary>
        /// Set up each webcam and begin playing it, blit to RenderTextures to display the feed.
        /// </summary>
        private void InitializeWebcams(string mainWebcamName, string secondaryWebcamName)
        {
            Webcams.Add(new WebCamTexture(mainWebcamName, RequestedCameraWidth, RequestedCameraHeight));
            
            if (secondaryWebcamName != "-" && secondaryWebcamName != "" && secondaryWebcamName != mainWebcamName)
                Webcams.Add(new WebCamTexture(secondaryWebcamName, RequestedCameraWidth, RequestedCameraHeight));

            for (int i = 0; i < Webcams.Count; i++)
            {
                Webcams[i].Play();
                Blit(i);
            }
        }

        /// <summary>
        /// Blit the webcam feed to the corresponding RenderTexture.
        /// </summary>
        /// <param name="webcamIndex"></param>
        private void Blit(int webcamIndex)
        {          
            if (RenderTextures.Count > webcamIndex)
                Graphics.Blit(Webcams[webcamIndex], RenderTextures[webcamIndex]);
        }


        /// <summary>
        /// Coroutine to take periodic snapshots while emotes are present in the webcam area.
        /// </summary>
        /// <returns></returns>
        private IEnumerator TakeSnapshotCoroutine()
        {
            // Wait until the end of frame to ensure all events are processed and EmojisAreInActionArea is true
            yield return new WaitForEndOfFrame();
            
            // Interval between each snapshot.
            float interval = 1f / TargetSnapshotFPS;
            float firstPostTime = Time.realtimeSinceStartup;
            float nextPostTime = Time.realtimeSinceStartup + interval;

            int count = 0;
            
            while (EmojisInWebcamArea.Any())
            {
                TakeSnapshots();
                count++;
                EditorUIFerStats.Instance.SnapshotFPS = $"{Math.Round(count / (Time.realtimeSinceStartup - firstPostTime),1)}";

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

            _coroutine = null;
        }

        /// <summary>
        /// Capture and process a snapshot from each active webcam.
        /// </summary>
        private static void TakeSnapshots()
        {
            Profiler.BeginSample("TakeSnapshots");
            
            // Initialize a new Snapshot
            Snapshot snapshot = new()
            {
                Timestamp = LoggingSystem.GetUnixTimestamp(),
                LevelID =  GameManager.Instance.Level.LevelName,
                LevelMode = GameManager.Instance.Level.LevelMode,
                Emoji = EmojiInWebcamArea,
                ImageTextures = new List<Color32[]>(),
            };
        
            // Capture a single frame for each webcam
            foreach (WebCamTexture webcam in Webcams)
            {
                Profiler.BeginSample("GetPixels");
                Color32[] pixels = webcam.GetPixels32();
                snapshot.ImageTextures.Add(pixels);
                Profiler.EndSample();
            }
            
            // Add the Snapshot to the List of Snapshots in the LoggingSystem
            LoggingSystem.Instance.LatestSnapshot = snapshot;

            Profiler.EndSample();
        }

        public static Snapshot GetSnapshot() => LoggingSystem.Instance.LatestSnapshot;

        /// <summary>
        /// Convert the snapshot to a base64 string for network transmission.
        /// </summary>
        public static string GetBase64(Snapshot snapshot)
        {
            Profiler.BeginSample("SetPixels");
            // Convert pixels to a texture
            _texture.SetPixels32(snapshot.ImageTextures[0]);
            _texture.Apply();
            Profiler.EndSample();
                
            Profiler.BeginSample("EncodeToJPG");
            // Encode frame as JPG
            byte[] image = _texture.EncodeToJPG();
            Profiler.EndSample();

            Profiler.BeginSample("ToBase64String");
            // Convert to frame to base64
            string base64 = Convert.ToBase64String(image);
            Profiler.EndSample();

            // Return the base64-encoded image
            return base64;
        }
    }
}