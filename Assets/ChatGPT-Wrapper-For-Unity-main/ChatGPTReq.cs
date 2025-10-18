using System;
using System.Collections.Generic;

namespace ChatGPTWrapper {
    // Chat Completions API
    [Serializable]
    public class ChatCompletionReq
    {
        public string model;
        public List<ChatMessage> messages;
        public float temperature = 0.7f;
        public int max_tokens = 500;
    }

    [Serializable]
    public class ChatMessage
    {
        public string role;
        public string content;
    }

    // Responses API
    [Serializable]
    public class ResponsesReq
    {
        public string model;
        public string input;
        public string instructions;
    }

    [Serializable]
    public class InputMessage
    {
        public string role;
        public string content;
    }

    // Legacy 지원
    [Serializable]
    public class ChatGPTReq
    {
        public string model;
        public string prompt;
        public int max_tokens;
        public float temperature;
    }
}
