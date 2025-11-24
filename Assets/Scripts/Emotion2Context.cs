using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Emotion2Context : MonoBehaviour
{
    private FerHandler _ferHandler;
    // Start is called before the first frame update
    void Start()
    {
        _ferHandler = FindObjectOfType<FerHandler>();
    }

    // Update is called once per frame
    void Update()
    {
        if (_ferHandler != null)
        {
            var emotion = _ferHandler.CurrentWindowEmotion;
            EditorUI.EditorUI.Instance.UpdateCurrentEmotion(emotion);
        }
    }
}
