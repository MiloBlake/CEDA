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
        return jsonify({"result": float(pd.to_numeric(dataset[col], errors="coerce").mean())})
    if intent == "sum" and col:
        return jsonify({"result": float(pd.to_numeric(dataset[col], errors="coerce").sum())})
    if intent == "max" and col:
        return jsonify({"result": float(pd.to_numeric(dataset[col], errors="coerce").max())})
    if intent == "min" and col:
        return jsonify({"result": float(pd.to_numeric(dataset[col], errors="coerce").min())})
    if intent == "count":
        return jsonify({"result": int(len(dataset))})
    if intent == "list" and col:
        return jsonify({"values": dataset[col].head(50).tolist()})

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
        resp = llm(prompt, max_tokens=64, temperature=0.0, top_p=1.0)
        text = resp["choices"][0].get("text", "").strip()

        m = re.search(r"\{.*\}", text, re.S)
        if m:
            parsed = json.loads(m.group())
            op = parsed.get("operation")
            col = parsed.get("column")

            if op == "count":
                return jsonify({"result": int(len(dataset))})
            if op == "list" and col in cols:
                return jsonify({"values": dataset[col].head(50).tolist()})
            if col in cols:
                s = pd.to_numeric(dataset[col], errors="coerce")
                if op == "avg":  return jsonify({"result": float(s.mean())})
                if op == "sum":  return jsonify({"result": float(s.sum())})
                if op == "max":  return jsonify({"result": float(s.max())})
                if op == "min":  return jsonify({"result": float(s.min())})

        return jsonify({"response": text})

    return jsonify({"response": "Could not understand"})

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)