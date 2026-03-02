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

      const isHistogram = tr?.meta?.kind === "histogram";
      if (type === "histogram" || (type === "bar" && isHistogram)) {
        const histCol = tr?.meta?.col;
        const hasRangeSelection =
          !!selectedCategory?.col &&
          Array.isArray(selectedCategory?.ranges) &&
          selectedCategory.ranges.length > 0 &&
          selectedCategory.col === histCol;

        if (!hasRangeSelection) return tr;

        const selectedRanges = selectedCategory.ranges.map(([a, b]) => [
          Number(a),
          Number(b),
        ]);
        const ranges = tr.customdata || [];

        const isSelected = ranges.map((val) => {
          const [low, high] = val || [];
          return selectedRanges.some(
            ([a, b]) => Number(low) === a && Number(high) === b,
          );
        });
        return {
          ...tr,
          marker: {
            ...(tr.marker || {}),
            opacity: isSelected.map((s) => (s ? 1 : 0.25)),
            line: {
              color: isSelected.map((s) => (s ? "#111" : "rgba(0,0,0,0.35)")),
              width: isSelected.map((s) => (s ? 2 : 1.5)),
            },
          },
        };
      }

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
              width: labels.map((l) => (selectedSet.has(l) ? 2.5 : 1.5)),
            },
          },
        };
      }
      // Other chart type
      return tr;
    });
  }

  // For mobile: truncate long categorical axis labels and set the tick angle
  function truncateAxis(axis, values, maxLen = 12, tickangle = 90) {
    if (!values || !values.length) return axis;

    const tickvals = values.map(String);
    const ticktext = tickvals.map((v) =>
      v.length > maxLen ? v.slice(0, maxLen) + "…" : v,
    );

    return {
      ...(axis || {}),
      type: "category",
      tickmode: "array",
      tickvals,
      ticktext,
      tickangle,
      automargin: true,
    };
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

      const isMobile = window.innerWidth < 700;
      const layout = {
        ...message.chart.layout,
        autosize: true,
        height: isMobile ? 450 : 650,
        margin: isMobile ? { l: 95, r: 20, t: 40, b: 60 } : undefined,

        ...(isMobile
          ? {
              legend: {
                orientation: "h",
                x: 0.5,
                xanchor: "center",
                y: -0.25,
                yanchor: "top",
              },
            }
          : {}),
      };

      // for mobile, convert vertical bar charts to horizontal, otherwise they look very cramped
      const isBar = data?.[0]?.type === "bar";
      if (isMobile && isBar) {
        // note axis lables
        const xTitle = layout?.xaxis?.title?.text ?? layout?.xaxis?.title ?? "";
        const yTitle = layout?.yaxis?.title?.text ?? layout?.yaxis?.title ?? "";

        // flip vertical bars to horizontal bars
        data = data.map((tr) => ({
          ...tr,
          orientation: "h",
          x: tr.y,
          y: tr.x,
        }));

        layout.xaxis = {
          ...(layout.xaxis || {}),
          title: { text: yTitle || xTitle },
          automargin: true,
          tickangle: 0,
        };
        layout.yaxis = {
          ...(layout.yaxis || {}),
          title: null,
          tickmode: "array",
          tickfont: { size: 10 },
        };

        layout.height = 520; // give enough space for names
        layout.margin = { l: 40, r: 20, t: 50, b: 60 };
      }

      if (isMobile) {
        const t0 = data?.[0];
        const tickAngle = isBar ? 0 : 90;

        // truncate categorical X axis
        if (t0?.x && typeof t0.x[0] === "string") {
          layout.xaxis = truncateAxis(layout.xaxis, t0.x, 12, tickAngle);
        }

        // truncate categorical Y axis
        if (t0?.y && typeof t0.y[0] === "string") {
          layout.yaxis = truncateAxis(layout.yaxis, t0.y, 12, tickAngle);
        }
      }

      // interaction type
      layout.dragmode = isScatter ? "select" : false;
      layout.clickmode = isMobile ? false : "event";
      layout.hovermode = isMobile ? false : "closest";

      return (
        <div style={{ width: "100%", overflowX: "auto", minWidth: "320px" }}>
          <div>
            <Plot
              key={`chart-${i}-${message.chart?.layout?.title?.text || "untitled"}`}
              data={data}
              layout={layout}
              config={{
                responsive: true,
                displaylogo: false,
                displayModeBar: !isMobile,
                scrollZoom: !isMobile,
              }}
              useResizeHandler
              style={{ width: "100%", height: isMobile ? "420px" : "650px" }}
              onInitialized={(fig, graphDiv) => {
                // Disable tapping selection on mobile
                if (isMobile) return;

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

                  const isHistogram = pt?.data?.meta?.kind === "histogram";

                  if (isHistogram) {
                    const range = pt.customdata;
                    col = pt?.data?.meta?.col;

                    if (!range || range.length !== 2) return;

                    const [low, high] = range.map(Number);

                    // Update selectedCategory for histogram bins
                    setSelectedCategory((prev) => {
                      if (
                        !prev ||
                        prev.col !== col ||
                        !Array.isArray(prev.ranges)
                      ) {
                        return { col, ranges: [[low, high]] };
                      }

                      const exists = prev.ranges.some(
                        ([a, b]) => Number(a) === low && Number(b) === high,
                      );
                      if (exists) {
                        const next = prev.ranges.filter(
                          ([a, b]) =>
                            !(Number(a) === low && Number(b) === high),
                        );
                        console.log("Histogram bin deselected:", col, [
                          low,
                          high,
                        ]);
                        return next.length ? { col, ranges: next } : null;
                      } else {
                        console.log("Histogram bin selected:", col, [
                          low,
                          high,
                        ]);
                        return { col, ranges: [...prev.ranges, [low, high]] };
                      }
                    });
                    return;
                  }

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
              onSelected={
                isMobile
                  ? undefined
                  : (e) => {
                      const pts = e?.points || [];
                      const ids = pts
                        .map((p) => p.customdata?.[0])
                        .filter((v) => v != null);
                      if (!ids.length) return;
                      setSelectedRowIds([...new Set(ids)]);
                    }
              }
              onDeselect={
                isMobile
                  ? undefined
                  : () => {
                      setSelectedRowIds([]);
                    }
              }
            />
          </div>
        </div>
      );
    }

    return <div style={{ whiteSpace: "pre-wrap", wordWrap: "break-word" }}>{message}</div>;
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
