using UnityEngine;
using System.Collections.Generic;
using UnityEngine.Events;
using System;
using Newtonsoft.Json;

namespace ChatGPTWrapper {

    public class ChatGPTConversation : MonoBehaviour
    {
        //[Header("Parameters")]
        //[SerializeField]
        //private string _apiKey = null;

        public enum AIModel
        {
            gpt_5_nano_2025_08_07
        }

        [Header("Model Settings")]
        [SerializeField]
        private AIModel _selectedAIModel = AIModel.gpt_5_nano_2025_08_07;
        private string _model;
        
        private string _uri = "https://api.openai.com/v1/responses";
        private List<(string, string)> _reqHeaders;
        

        private Requests requests = new Requests();
        private Prompt _prompt;
        private string _lastUserMsg;
        private string _lastChatGPTMsg;

        [Header("Prompt")]
        [SerializeField]
        public string _chatbotName = "ChatGPT";

        [TextArea(4,6)]
        [SerializeField]
        public string _initialPrompt = "You are a helpful AI assistant.";

        [Space(15)]
        public UnityStringEvent chatGPTResponse = new UnityStringEvent();

        private void Start()
        {
            // Set model based on selection
            switch (_selectedAIModel)
            {
                case AIModel.gpt_5_nano_2025_08_07:
                    _model = "gpt-5-nano-2025-08-07";
                    break;
            }

            // Ensure we have a default English prompt if empty
            if (string.IsNullOrEmpty(_initialPrompt))
            {
                _initialPrompt = "You are a helpful AI assistant.";
            }
            
            _prompt = new Prompt(_chatbotName, _initialPrompt);
            _reqHeaders = new List<(string, string)>
            { 
                ("Authorization", $"Bearer {Credentials.OpenAI_ApiKey}"),
                ("Content-Type", "application/json")
            };
        }

        public void SendToChatGPT(string message)
        {
            _lastUserMsg = message;
            _prompt.AppendText(Prompt.Speaker.User, message);

            // Responses API Request
            ResponsesReq reqObj = new ResponsesReq();
            reqObj.model = _model;
            reqObj.input = message;
            
            // Only include instructions if not empty
            if (!string.IsNullOrEmpty(_prompt.Instructions))
            {
                reqObj.instructions = _prompt.Instructions;
            }

            // Use Newtonsoft.Json to properly serialize with null value handling
            var settings = new JsonSerializerSettings 
            { 
                NullValueHandling = NullValueHandling.Ignore,
                DefaultValueHandling = DefaultValueHandling.Ignore
            };
            string json = JsonConvert.SerializeObject(reqObj, settings);
            Debug.Log("Sending to Responses API: " + json);
            
            StartCoroutine(requests.PostReq<ResponsesRes>(_uri, json, ResolveResponsesResponse, _reqHeaders));
        }

        private void ResolveResponsesResponse(ResponsesRes res)
        {
            // Extract text from output array
            if (res.output != null && res.output.Count > 0)
            {
                string allText = "";
                foreach (var outputMsg in res.output)
                {
                    if (outputMsg.role == "assistant" && outputMsg.content != null)
                    {
                        foreach (var contentItem in outputMsg.content)
                        {
                            if (contentItem.type == "output_text" && !string.IsNullOrEmpty(contentItem.text))
                            {
                                allText += contentItem.text;
                            }
                        }
                    }
                }
                _lastChatGPTMsg = allText;
            }
            else
            {
                _lastChatGPTMsg = "No response from API";
            }

            Debug.Log("ChatGPT Response: " + _lastChatGPTMsg);
            _prompt.AppendText(Prompt.Speaker.ChatGPT, _lastChatGPTMsg);
            ExManager._OnChatGPTResponse.Invoke(_lastChatGPTMsg);
        }
    }
}
