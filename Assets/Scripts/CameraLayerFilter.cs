// Example: Make the camera ignore the "Invisible" layer
using UnityEngine;

public class CameraLayerFilter : MonoBehaviour
{
    public Camera cam;
    public string layerToIgnore = "Components";

    void Start()
    {
        if (cam == null) cam = Camera.main;

        // Convert layer name to layer mask
        int layerMask = 1 << LayerMask.NameToLayer(layerToIgnore);

        // Remove that layer from the camera's culling mask
        cam.cullingMask &= ~layerMask;
    }
}

