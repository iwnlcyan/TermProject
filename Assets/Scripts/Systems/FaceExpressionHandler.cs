using UnityEngine;

namespace Systems
{
    /// <summary>
    /// Logs face expressions by interfacing with OVRPlugin's face tracking capabilities.
    /// </summary>
    public class FaceExpressionHandler
    {
        // Use preprocessor directives to conditionally compile code based on whether the OVRPlugin supports the current platform.
#if OVR_PLUGIN
        // Store the current face state retrieved from OVRPlugin.
        private OVRPlugin.FaceState _currentFaceState;
#endif

        /// <summary>
        /// Initializes the FaceExpressionLogger by starting the face and eye tracking features.
        /// </summary>
        public FaceExpressionHandler()
        {
#if OVR_PLUGIN
            // Attempt to start face tracking and log a warning if it fails.
            if (!OVRPlugin.StartFaceTracking())
                Debug.LogWarning($"[{nameof(OVRFaceExpressions)}] Failed to start face tracking.");

            // Attempt to start eye tracking and log a warning if it fails.
            if (!OVRPlugin.StartEyeTracking())
                Debug.LogWarning($"[{nameof(OVRFaceExpressions)}] Failed to start eye tracking.");
#endif
        }

        /// <summary>
        /// Retrieves the current face expressions and serializes them as a JSON string.
        /// </summary>
        /// <returns>A JSON representation of the current face expressions if valid, otherwise returns null.</returns>
        public string GetFaceExpressionsAsJson()
        {
#if OVR_PLUGIN
            // Check if face state is available and valid, then serialize to JSON.
            if (OVRPlugin.GetFaceState(OVRPlugin.Step.Render, -1, ref _currentFaceState) &&
                _currentFaceState.Status.IsValid)
                return JsonUtility.ToJson(_currentFaceState);

            // If the face expression data is not valid, log a warning.
            Debug.LogWarning($"[{nameof(FaceExpressionHandler)}] Face expression not valid.");
#endif

            // Return null if face expressions cannot be retrieved or if not supported.
            return null;
        }
        
    }
}