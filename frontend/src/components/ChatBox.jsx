import { useState } from "react";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const send = async () => {
    if (!input.trim()) return;
    
    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });
      const data = await res.json();
      const botResponse = data.result !== undefined ? data.result : JSON.stringify(data);
      setMessages([...messages, { user: input, bot: botResponse }]);
      setInput("");
    } catch (err) {
      setMessages([...messages, { user: input, bot: `Error: ${err.message}` }]);
      setInput("");
    }
  };

  return (
    <div>
      <div>
        {messages.map((m, i) => (
          <div key={i}>
            <p><b>User:</b> {m.user}</p>
            <p><b>Bot:</b> {m.bot}</p>
          </div>
        ))}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === "Enter" && send()}
        placeholder="Ask a question..."
      />
      <button onClick={send}>Send</button>
    </div>
  );
}