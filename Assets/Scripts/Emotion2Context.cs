using Enums;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Emotion2Context : MonoBehaviour
{
    private FerHandler _ferHandler;
    public EEmote CurrentEmotion = EEmote.Neutral;

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
            CurrentEmotion = _ferHandler.CurrentWindowEmotion;
            if (EditorUI.EditorUI.Instance != null)
            {
                EditorUI.EditorUI.Instance.UpdateCurrentEmotion(CurrentEmotion);
            }
        }
    }
}
