using ChatGPTWrapper;
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GPT_Personality : MonoBehaviour
{
    public bool personalityEnabled;
    
    public enum Character { DarthVader, LukeSkywalker, Yoda, Chewbacca, CaptainAmerica, IronMan, Thor, Hulk, BlackWidow, Gandalf, Sauron, Frodo, Gollum }   
    public enum Movie { StarWars, Avengers, LordOfTheRings }
    
    public Character character = Character.Yoda;
    public Movie movie = Movie.StarWars;
    public ChatGPTConversation conversation;
    
    [TextArea(10,10)]
    public string customPrompt = "You are #Personality# from #Film#. Respond in character.";
    
    private List<string> characterNames = new List<string> { 
        "Darth Vader", "Luke Skywalker", "Yoda", "Chewbacca", 
        "Captain America", "Iron Man", "Thor", "Hulk", "Black Widow", 
        "Gandalf", "Sauron", "Frodo Baggins", "Gollum" 
    };
    
    private List<string> movieNames = new List<string> { "Star Wars", "Avengers", "The Lord of the Rings" };
    
    void Awake()
    {
        if (personalityEnabled)
        {
            conversation._chatbotName = characterNames[(int)character];
            string composedPrompt = customPrompt.Replace("#Personality#", characterNames[(int)character]);
            composedPrompt = composedPrompt.Replace("#Film#", movieNames[(int)movie]);
            composedPrompt += " Always respond in English.";
            
            conversation._initialPrompt = composedPrompt;
        }
        else
        {
            // Default English prompt when personality is disabled
            if (string.IsNullOrEmpty(conversation._initialPrompt))
            {
                conversation._initialPrompt = "You are a helpful AI assistant. Respond in English.";
            }
        }
    }
}
