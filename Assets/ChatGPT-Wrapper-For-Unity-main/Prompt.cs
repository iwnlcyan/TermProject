using System.Collections.Generic;

namespace ChatGPTWrapper {
    public class Prompt
    {
        private string _initialPrompt;
        private string _chatbotName;
        private List<InputMessage> _messages;

        public Prompt(string chatbotName, string initialPrompt) {
            _initialPrompt = initialPrompt;
            _chatbotName = chatbotName;
            _messages = new List<InputMessage>();
            
            if (!string.IsNullOrEmpty(initialPrompt))
            {
                _messages.Add(new InputMessage {
                    role = "developer",
                    content = initialPrompt
                });
            }
        }

        // Legacy support
        private string _currentPrompt;
        public string CurrentPrompt { get { return _currentPrompt; } }

        // Responses API
        public List<InputMessage> Messages { get { return _messages; } }
        public string Instructions { get { return _initialPrompt; } }

        public enum Speaker {
            User,
            ChatGPT
        }

        public void AppendText(Speaker speaker, string text)
        {
            // Responses API
            string role = speaker == Speaker.User ? "user" : "assistant";
            _messages.Add(new InputMessage {
                role = role,
                content = text
            });

            // Legacy support
            if (_currentPrompt == null) _currentPrompt = _initialPrompt;
            switch (speaker)
            {
                case Speaker.User:
                    _currentPrompt += " \n User: " + text + " \n " + _chatbotName + ": ";
                    break;
                case Speaker.ChatGPT:
                    _currentPrompt += text;
                    break;
            }
        }
    }
}
