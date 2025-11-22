using System.Collections;
using Enums;
using Manager;
using UnityEngine;
using Utilities;

/// <summary>
/// Manages the Action Area Shader, adjusting properties when Emojis interact with the area.
/// </summary>
public class ActionAreaShader : MonoBehaviour
{
    [Tooltip("Material to be manipulated.")]
    private Material _material;

    // Shader property IDs for efficient access
    private int _originShaderID;
    private int _bottomColorShaderID;

    [Header("Height of color ramp")] [SerializeField]
    private float ShaderRampDuration = 0.3f;

    [SerializeField] private float LowGradientPosition = -0.6f;
    [SerializeField] private float HighGradientPosition = -0.1f;

    [Header("Color of color ramp")] [SerializeField]
    private float TimePressureColorRampDuration = 1;

    [SerializeField] private float ResetColorRampDuration = 0.5f;
    [SerializeField] private Color TimePressureColor = new(1f, 0.2f, 0f, 0.6f);
    [SerializeField] private Color ResetColor = new(1f, 0.4f, 0f, 0.5f);

    /// <summary>
    /// Initialization function, sets up the material and shader property IDs.
    /// </summary>
    private void Start()
    {
        // Fetching the material from the Renderer component
        _material = GetComponent<Renderer>().material;

        // Converting shader property names to IDs for efficient access
        _originShaderID = Shader.PropertyToID("_Origin");
        _bottomColorShaderID = Shader.PropertyToID("_BottomColor");

        // Setting initial shader property values
        _material.SetFloat(_originShaderID, LowGradientPosition);
        _material.SetColor(_bottomColorShaderID, ResetColor);
    }

    private void Awake()
    {
        EventManager.OnEmoteEnteredActionArea += EmoteEnteredActionAreaCallback;
        EventManager.OnEmoteExitedActionArea += EmoteExitedActionAreaCallback;
    }

    private void OnDestroy()
    {
        EventManager.OnEmoteEnteredActionArea -= EmoteEnteredActionAreaCallback;
        EventManager.OnEmoteExitedActionArea -= EmoteExitedActionAreaCallback;
    }

    /// <summary>
    /// Callback for when an emoji enters the area.
    /// </summary>
    private void EmoteEnteredActionAreaCallback(Emoji emoji)
    {
        // Stopping all ongoing coroutines to prevent interference
        StopAllCoroutines();

        // Starting shader property adjustments for emoji entry
        StartCoroutine(RampShader(HighGradientPosition));
        StartCoroutine(RampColor(TimePressureColor, TimePressureColorRampDuration));
    }

    /// <summary>
    /// Callback for when an emoji exits the area.
    /// </summary>
    private void EmoteExitedActionAreaCallback(Emoji emoji)
    {
        // Stopping all ongoing coroutines to prevent interference
        StopAllCoroutines();

        // Starting shader property adjustments for emoji exit
        StartCoroutine(RampShader(LowGradientPosition));
        StartCoroutine(RampColor(ResetColor, ResetColorRampDuration));
    }


    /// <summary>
    /// Gradually adjusts a shader property over time. This moves the shader up or down.
    /// </summary>
    /// <param name="end">The target value for the shader property.</param>
    private IEnumerator RampShader(float end)
    {
        float time = 0;
        float start = _material.GetFloat(_originShaderID);

        // Gradually adjusting the shader property over the specified duration
        while (time < ShaderRampDuration)
        {
            _material.SetFloat(_originShaderID, Mathf.SmoothStep(start, end, time / ShaderRampDuration));
            time += Time.deltaTime;
            yield return null;
        }
        
        _material.SetFloat(_originShaderID, end);
    }

    /// <summary>
    /// Gradually adjusts a color property of the material over time.
    /// </summary>
    /// <param name="end">The target color.</param>
    /// <param name="duration">The duration over which the color change should occur.</param>
    private IEnumerator RampColor(Color end, float duration)
    {
        float time = 0;
        Color start = _material.GetColor(_bottomColorShaderID);

        // Gradually adjusting the color property over the specified duration
        while (time < duration)
        {
            _material.SetColor(_bottomColorShaderID, Color.Lerp(start, end, time / duration));
            time += Time.deltaTime;
            yield return null;
        }
        
        _material.SetColor(_bottomColorShaderID, end);
    }
    
}