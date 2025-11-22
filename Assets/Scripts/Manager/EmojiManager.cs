using System;
using System.Collections;
using Enums;
using States.Emojis;
using TMPro;
using UnityEngine;
using Utilities;
using Random = UnityEngine.Random;

namespace Manager
{
    /// <summary>
    /// Manages the states and behaviors of an Emoji in the game.
    /// </summary>
    public class EmojiManager : MonoBehaviour
    {
        // The current state of the Emoji.
        private EmojiState _emojiState;
        
        // Instances of possible states the Emoji can be in.
        private readonly EmojiPreState _preState = new ();
        internal readonly EmojiIntraState IntraState = new ();
        internal readonly EmojiFulfilledState FulfilledState = new ();
        internal readonly EmojiFailedState FailedState = new ();
        internal readonly EmojiLeavingState LeavingState = new();
    
        // Serialized fields for Unity inspector assignment.
        [SerializeField] private Renderer EmojiRenderer;
        [SerializeField] internal Animator EmojiAnimator;
        [SerializeField] internal TMP_Text EmoteTitle;
            
        // Material and related properties of the Emoji.
        internal Material EmojiMaterial;
        internal readonly int Sprite = Shader.PropertyToID("_Sprite");
        internal readonly int DissolveAmount = Shader.PropertyToID("_DissolveAmount");
        internal readonly int FailedColorAmount = Shader.PropertyToID("_FailedColorAmount");
        internal readonly int SuccessColorAmount = Shader.PropertyToID("_SuccessColorAmount");
        
        // Time left for Emoji to stay in the active area and the size of the action area.
        // Used for score calculations
        internal float ActionAreaLeft;
        internal float ActionAreaSize;
        
        // Rigidbody component for physics interactions.
        internal Rigidbody Rigidbody;
        
        // Movement for the current level
        private Vector3 _movementSpeed;
        
        // Spawn time for Training level mode
        private DateTime _spawnTime;

        internal Emoji Emoji;


        private void Awake()
        {
            // Get components and calculate values needed later.
            Rigidbody = GetComponent<Rigidbody>();
            // create a copy of the material
            EmojiMaterial = EmojiRenderer.material;
            ActionAreaSize = GameManager.Instance.ActionAreaSize;
        }

        private void OnEnable()
        {
            // Initialize the Emoji in the pre state and subscribe to events.
            SwitchState(_preState);
        
            // Calculate movement based on Action Area direction and movement speed
            _movementSpeed = GameManager.Instance.ActionAreaTransform.forward * GameManager.Instance.Level.MovementSpeed;

            // Start the despawn timer if in Training mode
            if (GameManager.Instance.Level.LevelMode == ELevelMode.Training)
                StartCoroutine(DespawnTimer());
            
            EventManager.OnEmotionDetected += OnEmotionDetectedCallback;
            EventManager.OnLevelFinished += OnLevelFinishedCallback;
        }

        private void OnDisable()
        {
            EventManager.OnEmotionDetected -= OnEmotionDetectedCallback;
            EventManager.OnLevelFinished -= OnLevelFinishedCallback;
        }

        private void Update()
        {
            // Call the Update Event of the current state.
            _emojiState.Update(this);
            
            // Emoji movement
            if (_emojiState != LeavingState)
                transform.position -= _movementSpeed * Time.deltaTime;
        }

        /// <summary>
        /// Switches the current state of the Emoji.
        /// </summary>
        /// <param name="state">The new state to switch to.</param>
        internal void SwitchState(EmojiState state)
        {
            _emojiState = state;
            _emojiState.EnterState(this);
        }

        // Callback for FER response event. emote is the emotion with the highest probability.
        private void OnEmotionDetectedCallback(EEmote emote) => _emojiState.OnEmotionDetectedCallback(this, emote);

        // Callback for level stopped event.
        // ReSharper disable Unity.PerformanceAnalysis
        private void OnLevelFinishedCallback()
        {
            _emojiState.Despawn(this);
        }

        private void OnTriggerEnter(Collider other) => _emojiState.OnTriggerEnter(other, this);

        private void OnTriggerExit(Collider other) => _emojiState.OnTriggerExit(other, this);
        
        // ReSharper disable Unity.PerformanceAnalysis
        /// <summary>
        /// Despawn the Emoji in training level mode
        /// </summary>
        /// <returns></returns>
        private IEnumerator DespawnTimer()
        {
            float timer = GameManager.Instance.Level.Count > 0 ? GameManager.Instance.Level.Count : 5f;
            yield return new WaitForSeconds(timer);
            _emojiState.Despawn(this);
        }

        public void FadeOut() => StartCoroutine(FadeOutCoroutine());

        /// <summary>
        /// Fades out the Emoji and deactivates it.
        /// </summary>
        private IEnumerator FadeOutCoroutine()
        {
            // If in training mode, fade out quickly. Otherwise, disable kinematic, apply a physics effect and fade out more slowly.
            if (GameManager.Instance.Level.LevelMode == ELevelMode.Training)
            {
                yield return StartCoroutine(MathHelper.SLerp(0, 1, 1f, EmojiRenderer.material, DissolveAmount));
            }
            else
            {
                Rigidbody.isKinematic = false;
                
                // Apply a random sidewards velocity to create a tumbling effect as the emoji fades out.
                Rigidbody.velocity = - _movementSpeed + GameManager.Instance.ActionAreaTransform.right * Random.Range(-0.05f, 0.05f);
                
                yield return StartCoroutine(MathHelper.SLerp(0, 1, 6f, EmojiRenderer.material, DissolveAmount));
            }
            
            DeactivateEmoji();
        }

        private void DeactivateEmoji()
        {
            gameObject.SetActive(false);
        }
    }
}
