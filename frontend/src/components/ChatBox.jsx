import { useState } from "react";
import "./styles/ChatBox.css";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const send = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    setInput("");
    setMessages(prev => [...prev, { user: userMessage, bot: null }]);
    
    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage }),
      });
      const data = await res.json();
      
      let botResponse;
      if (data.result !== undefined) botResponse = `${data.result}`;
      else if (data.values) botResponse = `Values: ${data.values.join(", ")}`;
      else botResponse = JSON.stringify(data);
      
      setMessages(prev => 
        prev.map((m, i) => 
          i === prev.length - 1 ? { ...m, bot: botResponse } : m
        )
      );
    } catch (err) {
      setMessages(prev => 
        prev.map((m, i) => 
          i === prev.length - 1 ? { ...m, bot: `Error: ${err.message}` } : m
        )
      );
    }
  };

  return (
    <div className="chatbox-container">
      {/* Messages Area */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-icon"></div>
            <p>Hi 👋 I'm ready to analyse your data!</p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className="message-group">
            {/* User Message */}
            <div className="user-message-container">
              <div className="user-message">
                {m.user}
              </div>
            </div>

            {/* Bot Message or Typing */}
            <div className="bot-message-container">
              <div className="bot-avatar">💭</div>
              
              {m.bot ? (
                <div className="bot-message">{m.bot}</div>
              ) : (
                <div className="bot-message">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-container">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask a question..."
            className="message-input"
          />
          <button
            onClick={send}
            disabled={!input.trim()}
            className="send-button"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}