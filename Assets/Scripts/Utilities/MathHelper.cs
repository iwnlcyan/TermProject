using System;
using System.Collections;
using System.Threading.Tasks;
using UnityEngine;

namespace Utilities
{
    /// <summary>
    /// Provides mathematical helper functions, particularly for smooth interpolation.
    /// </summary>
    public abstract class MathHelper
    {
        /// <summary>
        /// Smoothly interpolates a material's float property over time.
        /// </summary>
        public static IEnumerator SLerp(float from, float to, float duration, Material material, int nameID)
        {
            float t = 0;
            while (t < duration)
            {
                float result = Mathf.SmoothStep(from, to, t / duration);
                t += Time.deltaTime;
                material.SetFloat(nameID, result);

                yield return new WaitForEndOfFrame();
            }

            material.SetFloat(nameID, to);
        }
        
        /// <summary>
        /// Asynchronously smoothly interpolates a material's float property over time.
        /// </summary>
        public static async Task SLerpAsync(float from, float to, float duration, Material material, int nameID)
        {
            float t = 0;
            while (t < duration)
            {
                try
                {
                    float result = Mathf.SmoothStep(from, to, t / duration);
                    t += Time.deltaTime;
                    material.SetFloat(nameID, result);

                    await Task.Yield();
                }
                catch (Exception)
                {
                    return;
                }
            }

            // ReSharper disable once Unity.PerformanceCriticalCodeNullComparison
            if (material != null)
                material.SetFloat(nameID, to);
        }
        
        /// <summary>
        /// Smoothly interpolates the time scale over time.
        /// </summary>
        public static IEnumerator SLerpTimeScale(float from, float to, float duration)
        {
            float t = 0;
            while (t < duration)
            {
                float result = Mathf.SmoothStep(from, to, t / duration);
                t += Time.unscaledDeltaTime;
                Time.timeScale = result;
                yield return new WaitForEndOfFrame();
            }

            Time.timeScale = to;
        }
    }
}