Shader "Custom/Invisible"
{
    Properties
    {
        _Color("Color", Color) = (1,1,1,0)
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" }

        // No culling if you want it to be double-sided (optional)
        Cull Off

        // Blending for transparency
        Blend SrcAlpha OneMinusSrcAlpha

        // Turn off ZWrite if you don’t want it to block other objects
        ZWrite Off

        Pass
        {
            // Nothing is drawn
            ColorMask 0
        }
    }
    FallBack "Diffuse"
}
