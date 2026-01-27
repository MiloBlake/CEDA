import { useEffect, useRef, useState } from "react";
import Plot from 'react-plotly.js';
import "./styles/ChatBox.css";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [selectedRowIds, setSelectedRowIds] = useState([]); // Used for scatter chart interactions
  const [selectedCategory, setSelectedCategory] = useState(null); // Used for bar chart interactions -- { col: string, values: string[] } | null

  const send = async () => {
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    if (!userMessage) return;
    setInput("");
    setMessages(prev => [
      ...prev,
      { user: userMessage, bot: "__typing__" }
    ]);

    console.log("Sending query:", userMessage);
    console.log("Selected row IDs:", selectedRowIds);
    console.log("Selected category:", selectedCategory);
    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage, selected_row_ids: selectedRowIds, selected_category: selectedCategory }),
      });
      const data = await res.json();
      
      let botResponse;

      if (data.chart) {
        botResponse = {
          type: "chart",
          chart: JSON.parse(data.chart),
          message: data.message || "Here's your chart:"
        };
      }
      else if (data.result !== undefined) botResponse = `${data.result}`;
      else if (data.values) botResponse = `Values: ${data.values.join(", ")}`;
      else if (data.response) botResponse = data.response;
      else botResponse = JSON.stringify(data);

      setMessages(prev => {
        // Replace the last "__typing__" message with the bot response
        const updated = prev.map((m, idx) =>
        idx === prev.length - 1 && m.bot === "__typing__"
          ? { ...m, bot: botResponse }   
          : m
        );
        return updated;
      });
    } catch (err) {
      setMessages(prev => 
        prev.map((m, i) => 
          i === prev.length - 1 ? { ...m, bot: `Error: ${err.message}` } : m
        )
      );
    }
    //setSelectedRowIds([]); // Clear selection after each query
  };

  const renderMessage = (message, i) => {
    if (typeof message === "object" && message.type === "chart") {
      const isBar = message.chart?.data?.[0]?.type === "bar";
      const data = isBar
        ? message.chart.data.map(tr => ({
            ...tr,
            selected: { marker: { opacity: 1 } },
            unselected: { marker: { opacity: 1 } },
          }))
        : message.chart.data;

      const layout = {
        ...message.chart.layout,
        autosize: true,
      };
      delete layout.width;
      delete layout.height;
      // Disable dragmode selection for certain charts
      layout.dragmode = isBar ? false : "select";
      layout.clickmode = isBar ? "event+select" : "event";

      return ( 
        <div>
            <Plot
              key={`chart-${i}-${message.chart?.layout?.title?.text || "untitled"}`}
              data={data}
              layout={layout}
              config={{ responsive: true, displaylogo: false }}
              style={{ width: "100%", height: "650px" }}

              onInitialized={(fig, graphDiv) => {
                // Remove any previous handler 
                if (graphDiv.removeListener) graphDiv.removeAllListeners("plotly_click");

                graphDiv.on("plotly_click", (ev) => {
                  const pt = ev?.points?.[0];
                  if (!pt) return;

                  const isBarLocal = pt?.data?.type === "bar";
                  if (!isBarLocal) return;

                  const xVal = String(pt.x);
                  const xCol =
                    fig?.layout?.xaxis?.title?.text ||
                    fig?.layout?.xaxis?.title;

                  if (!xCol) return;

                  const isShift = !!ev?.event?.shiftKey;

                  setSelectedCategory((prev) => {
                    if (!prev || prev.col !== xCol) return { col: xCol, values: [xVal] };

                    const has = prev.values.includes(xVal);

                    // Shift-click removes
                    if (isShift) {
                      if (!has) return prev;
                      const next = prev.values.filter((v) => v !== xVal);
                      console.log("Bar removed:", xCol, xVal);
                      return next.length ? { col: xCol, values: next } : null;
                    }

                    // Normal click adds
                    if (has) return prev;
                    return { col: xCol, values: [...prev.values, xVal] };
                  });

                  console.log("Bars selected:", xCol, xVal);
                });
              }}
              
              // For scatter charts
              onSelected={(e) => {
                const pts = e?.points || [];
                const ids = pts.map((p) => p.customdata?.[0]).filter((v) => v != null);
                if (!ids.length) return;
                setSelectedRowIds([...new Set(ids)]);
              }}

              onDeselect={() => {
                setSelectedRowIds([]);
              }}
            />

        </div>
      );
    }
    
    return <div>{message}</div>;
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
              {m.user && (
                <div className="user-message-container">
                  <div className="user-message">{m.user}</div>
                </div>
              )}


            {/* Bot Message or Typing */}
            <div className="bot-message-container">
              <div className="bot-avatar">💭</div>
              
              {m.bot === "__typing__" && (
                <div className="bot-message">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              )}

              {m.bot && m.bot !== "__typing__" && (
                <div className={`bot-message ${m.bot?.type === "chart" ? "chart-message" : ""}`}>
                  {renderMessage(m.bot, i)}
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