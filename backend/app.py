import re
import json
import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_cpp import Llama
import pandas as pd
import io

from nlp_handler import parse_query
from graphs import render_chart

# Setup logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("backend")

dataset = None
llm = None

app = Flask(__name__)
CORS(app)

# Resolve model path 
MODEL_NAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "llm", MODEL_NAME)

llm = None
if os.path.exists(MODEL_PATH):
    try:
        llm = Llama(model_path=MODEL_PATH)
    except Exception as e:
        logger.exception("Model loading error")
        llm = None
else:
    logger.exception("Model file not found")

dataset = None

# UPLOAD DATASET - store DataFrame in memory
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
    if dataset is None:
        return jsonify({"response": "No dataset uploaded."}), 400
    cols = list(dataset.columns)

    spec = parse_query(q, cols, llm=llm)
    if not spec:
        return jsonify({"response": "Could not understand the query."})
    
    operation = spec.get("operation")
    col = spec.get("col")
    
    # Attempt direct nlp handling first
    if operation == "avg" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").mean()), 2)})
    if operation == "sum" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").sum()), 2)})
    if operation == "max" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").max()), 2)})
    if operation == "min" and col:
        return jsonify({"result": round(float(pd.to_numeric(dataset[col], errors="coerce").min()), 2)})
    if operation == "count":
        return jsonify({"result": int(len(dataset))})
    if operation == "list" and col:
        return jsonify({"values": dataset[col].head(50).tolist()})

    # Chart generation
    if operation == "chart":
        chart_spec = spec.get("chart", {})

        if not chart_spec:
            return jsonify({"response": "I can create charts, but I need more specific information."})
                
        try:
            logger.info(f"Generating chart with spec: {chart_spec}")
            chart = render_chart(dataset, chart_spec)
            return jsonify({"chart": chart.to_json(), "message": "Chart generated successfully."})
        except Exception as e:
            return jsonify({"response": f"Error generating chart: {str(e)}"})
        
    return jsonify({"response": "Could not understand"})

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)