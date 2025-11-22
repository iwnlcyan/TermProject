using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Enums;
using UnityEngine;
using Utilities;

namespace Manager
{
    /// <summary>
    /// Manages audio feedback for game events, playing specific sounds for level start, level stop, emote success, and emote failure.
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        [SerializeField] private AudioSource MusicAudioSource; // Background music audio source
        [SerializeField] private AudioSource EffectAudioSource; // Sound effects audio source
        [SerializeField] private AudioClip FailSound; // Sound to play on emote fail
        [SerializeField] private AudioClip SuccessSound; // Sound to play on emote success
        [SerializeField] private AudioClip LevelStartSound; // Sound to play when level starts
        [SerializeField] private AudioClip LevelStoppedSound; // Sound to play when level stops
        [SerializeField] private List<AudioClip> MusicClips; // List of music clips to play when playing a level
        
        private int _lastMusicClip; // Index of last played music clip
        private float _musicVolume;
        private bool _levelPlaying;
        [SerializeField] private bool PlayMusicClips; // Whether music should be played

        private void OnEnable()
        {
            _musicVolume = MusicAudioSource.volume;
            
            // Subscribe to game event notifications
            EventManager.OnLevelStarted += OnLevelStartedCallback;
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
            EventManager.OnEmoteFulfilled += OnEmoteFulfilledCallback;
            EventManager.OnEmoteFailed += OnEmoteFailedCallback;
        }

        private void OnDestroy()
        {
            // Unsubscribe from game event notifications
            EventManager.OnLevelStarted -= OnLevelStartedCallback;
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
            EventManager.OnEmoteFulfilled -= OnEmoteFulfilledCallback;
            EventManager.OnEmoteFailed -= OnEmoteFailedCallback;
        }

        /// <summary>
        /// Callback for when the level starts, plays the start sound and begins level music.
        /// </summary>
        private void OnLevelStartedCallback()
        {
            _levelPlaying = true;
            
            // Play level started sound
            PlaySoundEffect(LevelStartSound);
            
            // Play music
            PlayMusic();
        }

        /// <summary>
        /// Plays the level music.
        /// </summary>
        private void PlayMusic()
        {
            if (!PlayMusicClips)
                return;
            
            // Determine which music clip to play.
            switch (MusicClips.Count)
            {
                // If there is only one music clip available, select it to be played.
                case 1:
                    MusicAudioSource.clip = MusicClips.First();
                    break;
                // If there is more than one music clip, choose one at random.
                case > 1:
                {
                    // Generate a random index to select a music clip.
                    int index = Random.Range(0, MusicClips.Count);

                    // If the random index is the same as the last played clip, find a new index. This ensures variety in music playback.
                    while (index == _lastMusicClip)
                    {
                        index = Random.Range(0, MusicClips.Count);
                    }

                    // Set the selected music clip to the audio source.
                    MusicAudioSource.clip = MusicClips[index];
                    // Update the last music clip index to the one currently selected.
                    _lastMusicClip = index;
                    break;
                }
            }

            // Set the volume to full.
            MusicAudioSource.volume = _musicVolume;
            // Reset the playback position of the audio source to the beginning of the clip.
            MusicAudioSource.time = 0;
            // Play the selected music clip with a delay to allow the level start sound to be heard first.
            MusicAudioSource.PlayDelayed(0.9f);
        }

        private void OnLevelFinishedCallback() => LevelFinished();

        /// <summary>
        /// Callback for when the level stops, stops the music and plays the stop sound.
        /// </summary>
        private void LevelFinished()
        {
            if (!_levelPlaying)
                return;
            _levelPlaying = false;
            
            // Stop the music when the level stops
            StartCoroutine(FadeOutMusicCoroutine(1f));

            // Play level stopped sound
            PlaySoundEffect(LevelStoppedSound);
        }

        /// <summary>
        /// Callback for when an emote is successfully fulfilled, plays the success sound.
        /// </summary>
        private void OnEmoteFulfilledCallback(Emoji emoji, float score)
        {
            // Play success sound
            PlaySoundEffect(SuccessSound);
        }
        
        /// <summary>
        /// Callback for when an emote imitation fails, plays the fail sound.
        /// </summary>
        private void OnEmoteFailedCallback(Emoji emoji)
        {
            if (!_levelPlaying)
                return;
            
            // Play fail sound
            PlaySoundEffect(FailSound);
        }

        /// <summary>
        /// Plays a sound effect using the designated effects audio source.
        /// </summary>
        /// <param name="sound">The audio clip to play as a one-shot sound effect.</param>
        private void PlaySoundEffect(AudioClip sound)
        {
            if (sound != null)
                EffectAudioSource.PlayOneShot(sound);
        }
        
        /// <summary>
        /// Coroutine to smoothly fade out the music volume.
        /// </summary>
        /// <param name="duration">The duration over which to fade out the music.</param>
        private IEnumerator FadeOutMusicCoroutine(float duration)
        {
            _musicVolume = MusicAudioSource.volume;

            for (float t = 0; t < duration; t += Time.unscaledDeltaTime)
            {
                MusicAudioSource.volume = Mathf.Lerp(_musicVolume, 0, t / duration);
                yield return null;
            }

            MusicAudioSource.volume = 0; // Ensure the volume is set to 0
            MusicAudioSource.Stop(); // Stop the music after fading out
        }
    }
}