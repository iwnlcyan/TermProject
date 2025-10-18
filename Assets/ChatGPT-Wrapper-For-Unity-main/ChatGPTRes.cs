using System;
using System.Collections.Generic;

namespace ChatGPTWrapper {
    // Chat Completions API
    [Serializable]
    public class ChatCompletionRes
    {
        public string id;
        public string model;
        public List<ChatChoice> choices;
    }

    [Serializable]
    public class ChatChoice
    {
        public int index;
        public ChatMessage message;
        public string finish_reason;
    }

    // Responses API (Legacy)
    [Serializable]
    public class ResponsesRes
    {
        public string id;
        public List<OutputMessage> output;
        public string output_text;
    }

    [Serializable]
    public class OutputMessage
    {
        public string id;
        public string type;
        public string role;
        public List<OutputContent> content;
    }

    [Serializable]
    public class OutputContent
    {
        public string type;
        public string text;
    }

    // Legacy 응답
    [Serializable]
    public class ChatGPTRes
    {
        public string id;
        public List<Choices> choices;
    }
}
