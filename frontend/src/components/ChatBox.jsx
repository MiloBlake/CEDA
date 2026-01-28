import { useState } from "react";
import Plot from "react-plotly.js";
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
    setMessages((prev) => [...prev, { user: userMessage, bot: "__typing__" }]);

    console.log("Sending query:", userMessage);
    console.log("Selected row IDs:", selectedRowIds);
    console.log("Selected category:", selectedCategory);
    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage,
          selected_row_ids: selectedRowIds,
          selected_category: selectedCategory,
        }),
      });
      const data = await res.json();

      let botResponse;

      if (data.chart) {
        botResponse = {
          type: "chart",
          chart: JSON.parse(data.chart),
          message: data.message || "Here's your chart:",
        };
      } else if (data.result !== undefined) botResponse = `${data.result}`;
      else if (data.values) botResponse = `Values: ${data.values.join(", ")}`;
      else if (data.response) botResponse = data.response;
      else botResponse = JSON.stringify(data);

      setMessages((prev) => {
        // Replace the last "__typing__" message with the bot response
        const updated = prev.map((m, idx) =>
          idx === prev.length - 1 && m.bot === "__typing__"
            ? { ...m, bot: botResponse }
            : m,
        );
        return updated;
      });
    } catch (err) {
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1 ? { ...m, bot: `Error: ${err.message}` } : m,
        ),
      );
    }
    setSelectedRowIds([]); // Clear selection after each query
    setSelectedCategory(null); // Clear category selection after each query
  };

  function applyCategorySelection(traces, layout, selectedCategory) {
    // Apply category selection to bar and pie charts by adjusting opacity and outlines

    const hasSelection =
      !!selectedCategory?.col &&
      Array.isArray(selectedCategory?.values) &&
      selectedCategory.values.length > 0;

    const selectedSet = hasSelection
      ? new Set(selectedCategory.values.map(String))
      : new Set();

    const xCol = layout?.xaxis?.title?.text || layout?.xaxis?.title || null;

    return traces.map((tr) => {
      const type = tr?.type;

      // Bar chart
      if (type === "bar") {
        const xs = (tr.x || []).map(String);

        // Check if default selection applies
        const defaultSelectionApplies =
          hasSelection && xCol && selectedCategory?.col === xCol;

        return {
          ...tr,
          marker: {
            ...(tr.marker || {}),
            // dim only when selection applies
            opacity: defaultSelectionApplies
              ? xs.map((x) => (selectedSet.has(x) ? 1 : 0.25))
              : 1,

            // border stronger on selected bars
            line: {
              color: defaultSelectionApplies
                ? xs.map((x) =>
                    selectedSet.has(x) ? "#111" : "rgba(0,0,0,0.4)",
                  )
                : "rgba(0,0,0,0.3)",
              width: defaultSelectionApplies
                ? xs.map((x) => (selectedSet.has(x) ? 2 : 2))
                : 1.5,
            },
          },
        };
      }

      // Pie chart
      if (type === "pie") {
        const pieCol = tr?.meta?.col || null;
        if (!pieCol || selectedCategory?.col !== pieCol) return tr;

        const labels = (tr.labels || []).map(String);

        return {
          ...tr,
          pull: labels.map((l) => (selectedSet.has(l) ? 0.15 : 0)),
          marker: {
            ...(tr.marker || {}),
            opacity: labels.map((l) => (selectedSet.has(l) ? 1 : 0.35)),
            line: {
              color: labels.map((l) =>
                selectedSet.has(l) ? "#111" : "rgba(0,0,0,0)",
              ),
              width: labels.map((l) => (selectedSet.has(l) ? 2 : 0)),
            },
          },
        };
      }
      // Other chart type
      return tr;
    });
  }

  const renderMessage = (message, i) => {
    if (typeof message === "object" && message.type === "chart") {
      const isScatter = message.chart?.data?.[0]?.type === "scatter";

      let data = message.chart.data;
      if (!isScatter) {
        data = applyCategorySelection(
          message.chart.data,
          message.chart.layout,
          selectedCategory,
        );
      }

      const layout = {
        ...message.chart.layout,
        autosize: true,
      };

      delete layout.width;
      delete layout.height;

      // interaction type
      layout.dragmode = isScatter ? "select" : false;
      layout.clickmode = isScatter ? "event" : "event";

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
              if (graphDiv.removeListener)
                graphDiv.removeAllListeners("plotly_click");

              graphDiv.on("plotly_click", (ev) => {
                const pt = ev?.points?.[0];
                if (!pt) return;

                const isBarLocal = pt?.data?.type === "bar";
                const isPieLocal = pt?.data?.type === "pie";
                if (!isBarLocal && !isPieLocal) return;

                let value = null;
                let col = null;

                if (isBarLocal) {
                  value = String(pt.x);
                  col =
                    fig?.layout?.xaxis?.title?.text ||
                    fig?.layout?.xaxis?.title;
                } else if (isPieLocal) {
                  value = String(pt.label);
                  col = pt?.data?.meta?.col;
                }

                if (col == null || value == null) return;

                setSelectedCategory((prev) => {
                  if (!prev || prev.col !== col)
                    return { col: col, values: [value] };

                  const has = prev.values.includes(value);

                  // Remove selected value or add unselected value
                  if (has) {
                    const next = prev.values.filter((v) => v !== value);
                    console.log("Bar deselected:", col, value);
                    return next.length ? { col, values: next } : null;
                  } else {
                    console.log("Bar selected:", col, value);
                    return { col, values: [...prev.values, value] };
                  }
                });
              });
            }}
            // For scatter charts
            onSelected={(e) => {
              const pts = e?.points || [];
              const ids = pts
                .map((p) => p.customdata?.[0])
                .filter((v) => v != null);
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
                <div
                  className={`bot-message ${m.bot?.type === "chart" ? "chart-message" : ""}`}
                >
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
          {(selectedCategory || selectedRowIds.length > 0) && (
            <button
              type="button"
              className="reset-filters-button"
              onClick={() => {
                setSelectedCategory(null);
                setSelectedRowIds([]);
              }}
            >
              Reset filters
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
