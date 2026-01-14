import re
import json
import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_cpp import Llama
import pandas as pd
import io

from nlp_handler import detect_intent
from graphs import ChartGenerator, get_chart_suggestions

dataset = None
llm = None

app = Flask(__name__)
CORS(app)

# resolve model path 
MODEL_NAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "llm", MODEL_NAME)

llm = None
if os.path.exists(MODEL_PATH):
    try:
        llm = Llama(model_path=MODEL_PATH)
    except Exception as e:
        logging.exception("Failed to load Llama model")
        llm = None
else:
    logging.warning("LLM model not found at %s", MODEL_PATH)

dataset = None

# UPLOAD DATASET
@app.route("/upload", methods=["POST"])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        global dataset
        dataset = pd.read_csv(io.BytesIO(file.read()))
        return jsonify({
            "message": "File uploaded", 
            "columns": list(dataset.columns)
        })
    except Exception as e:
        print(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# QUERY
@app.route("/query", methods=["POST"])
def query():
    global dataset, llm
    q = (request.json or {}).get("query", "")
    cols = list(dataset.columns)

    col = next((c for c in cols if c.lower() in q.lower()), None)
    intent = detect_intent(q)

    # Attemtpt direct nlp handling first
    if intent == "avg" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").mean()), 2)})
    if intent == "sum" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").sum()), 2)})
    if intent == "max" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").max()), 2)})
    if intent == "min" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").min()), 2)})
    if intent == "count":
        return jsonify({"result": int(len(dataset))})
    if intent == "list" and col:
        return jsonify({"values": dataset[col].head(50).tolist()})

    # Chart generation
    if intent == "chart":
        suggestion = get_chart_suggestions(dataset, q)
        if suggestion:
            try:
                chart_gen = ChartGenerator(dataset)
                
                if suggestion["type"] == "scatter":
                    fig = chart_gen.create_scatter(suggestion["x"], suggestion.get("y"))
                elif suggestion["type"] == "histogram":
                    fig = chart_gen.create_histogram(suggestion["x"])
                elif suggestion["type"] == "box":
                    fig = chart_gen.create_box_plot(suggestion["x"], suggestion.get("group"))
                elif suggestion["type"] == "bar":
                    fig = chart_gen.create_bar_chart(suggestion["x"])
                
                return jsonify({
                    "chart": fig.to_json(),  # Change from chart_suggestion to chart
                    "message": f"Here's a {suggestion['type']} chart:"
                })
            except Exception as e:
                return jsonify({"response": f"Could not generate chart: {str(e)}"})
        else:
            return jsonify({"response": "I can create charts, but I need more specific information."})

    # Use LLM to attempt to parse complex queries
    if llm:
        prompt = (
            "You are a data analysis assistant.\n"
            "Your task is to reformulate the user's query so that an nlp can understand it.\n"
            "Rewrite the user's analytics query into single line JSON ONLY.\n"
            f"Columns: {', '.join(cols)}\n"
            'Schema: {"operation":"avg|sum|max|min|count|list","column":"<column name or null>"}\n'
            'Example 1: {"operation":"avg","column":"Age"}\n'
            'Example 2: {"operation":"count","column":null}\n'
            f"User: {q}\n"
        )

        try:
            resp = llm(prompt, max_tokens=64, temperature=0.0, top_p=1.0)
            text = resp["choices"][0].get("text", "").strip()
            
            # Remove any non-JSON content before JSON response
            text = text.replace("JSON response: ", "").strip()

            text_json = re.search(r'\{[^{}]*\}', text)
            if text_json:
                parsed = json.loads(text_json.group())
                op = parsed.get("operation")
                col = parsed.get("column")

                if op == "count":
                    return jsonify({"result": int(len(dataset))})
                if op == "list" and col in cols:
                    return jsonify({"values": dataset[col].head(50).tolist()})
                if col in cols:
                    s = pd.to_numeric(dataset[col], errors="coerce")
                    if op == "avg":  return jsonify({"result": round(float(s.mean()), 2)})
                    if op == "sum":  return jsonify({"result": round(float(s.sum()), 2)})
                    if op == "max":  return jsonify({"result": round(float(s.max()), 2)})
                    if op == "min":  return jsonify({"result": round(float(s.min()), 2)})

            return jsonify({"response": text})
        except Exception as e:
            return jsonify({"response": f"Error processing query: {str(e)}"})

    return jsonify({"response": "Could not understand"})

@app.route("/chart", methods=["POST"])
def generate_chart():
    global dataset
    if dataset is None:
        return jsonify({"error": "No dataset loaded"}), 400
    
    data = request.json
    chart_type = data.get("type", "scatter")
    x_col = data.get("x_column")
    y_col = data.get("y_column")
    color_col = data.get("color_column")
    group_col = data.get("group_column")
    
    try:
        chart_gen = ChartGenerator(dataset)
        
        if chart_type == "scatter":
            fig = chart_gen.create_scatter(x_col, y_col, color_col)
        elif chart_type == "histogram":
            fig = chart_gen.create_histogram(x_col, color_col)
        elif chart_type == "box":
            fig = chart_gen.create_box_plot(x_col, group_col)
        elif chart_type == "bar":
            fig = chart_gen.create_bar_chart(x_col, y_col)
        else:
            return jsonify({"error": "Unsupported chart type"}), 400
        
        return jsonify({
            "chart": fig.to_json(),
            "columns": list(dataset.columns),
            "numeric_columns": dataset.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": dataset.select_dtypes(include=['object', 'category']).columns.tolist()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)