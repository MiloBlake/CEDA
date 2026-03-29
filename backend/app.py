''' 
This is the main Flask application for the Data Analysis Chatbot backend.
It provides endpoints for uploading datasets, querying for insights and charts, and analysing user selections.
'''
import json
import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_cpp import Llama
import pandas as pd
import io
from typing import Any, Dict, List, Optional
import chardet

from nlp_handler import parse_query
from graphs import render_chart
from selection_analysis import build_selection_comparison_packet, run_llm_selection_analysis

# Setup logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("backend.app")

dataset = None
llm = None

app = Flask(__name__)
CORS(app)

# Resolve model path 
MODEL_NAME = "Phi-3.5-mini-instruct-Q3_K_M.gguf"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "llm", MODEL_NAME)

if os.path.exists(MODEL_PATH):
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=1024,
            n_threads=12,
            n_batch=256,
            use_mmap=True,
            f16_kv=True,
        )
        llm.create_chat_completion(
            messages=[{"role":"user","content":"ping"}],
            max_tokens=1
            )
    except Exception as e:
        logger.exception("Model loading error: %s", e)
else:
    logger.warning("Model file not found at %s", MODEL_PATH)


# UPLOAD DATASET - store DataFrame in memory
@app.route("/upload", methods=["POST"])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Try reading the file with pandas, with a fallback in the case of encoding issues
        global dataset
        try:
            dataset = pd.read_csv(io.BytesIO(file.read()))
        except UnicodeDecodeError:
            file.seek(0) # reset file pointer
            raw_file = file.read()
            # Use chardet to detect encoding method
            detected = chardet.detect(raw_file)
            encoding = detected.get('encoding', 'latin-1')
            dataset = pd.read_csv(io.BytesIO(raw_file), encoding=encoding)

        # Add a unique row identifier
        dataset = dataset.reset_index(drop=True)
        dataset["_row_id"] = dataset.index

        return jsonify({
            "message": "File uploaded! \n\nTry: 'list columns', 'average [column]', 'bar chart of [column] vs [column]', 'analyze'",
            "columns": list(dataset.columns)
        })
    except Exception as e:
        logger.exception("Upload error: %s", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def apply_selection(df: pd.DataFrame,
                    selected_ids: Optional[List[int]] = None,
                    selected_category: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Apply the UI selection onto df.
    Supports:
      - selected_row_ids: explicit row-id list
      - selected_category: {col, value|values|ranges} for categorical / histogram range selection
    """
    out = df

    # Category-based selection (bar/pie/hist bins)
    if selected_category and selected_category.get("col"):
        col_name = selected_category["col"]
        if col_name in out.columns:
            # numeric range selection (histogram bins)
            ranges = selected_category.get("ranges")
            if ranges:
                num = pd.to_numeric(out[col_name], errors="coerce")
                # Find rows that fall into any of the ranges
                mask = pd.Series(False, index=out.index)
                for r in ranges:
                    if not r or len(r) != 2:
                        continue
                    lo, hi = r
                    try:
                        lo_f = float(lo)
                        hi_f = float(hi)
                    except Exception:
                        continue
                    mask = mask | ((num >= lo_f) & (num < hi_f))
                out = out[mask]
            else:
                # categorical selection
                values = selected_category.get("values")
                if values:
                    out = out[out[col_name].astype(str).isin([str(v) for v in values])]
                else:
                    # single value
                    val = selected_category.get("value")
                    if val is not None:
                        out = out[out[col_name].astype(str) == str(val)]

    # Explicit row-id selection (scatter selections etc.)
    if selected_ids:
        if "_row_id" in out.columns:
            out = out[out["_row_id"].isin(selected_ids)]

    return out

# QUERY
@app.route("/query", methods=["POST"])
def query():
    global dataset, llm
    q = (request.json or {}).get("query", "")
    if dataset is None:
        return jsonify({"response": "No dataset uploaded."}), 400
    cols = list(dataset.columns)

    selected_ids = (request.json or {}).get("selected_row_ids") or []
    selected_category = (request.json or {}).get("selected_category")
    # Ensure selected_category is JSON serialisable
    selected_category = json.loads(json.dumps(selected_category, default=str)) if selected_category else None
    base_dataset = dataset
    selected_dataset = base_dataset

    selected_dataset = apply_selection(selected_dataset, selected_ids=selected_ids, selected_category=selected_category)

    # Quick check for if the user is asking for selection analysis
    q_clean = q.strip().lower()
    selection_exists = bool(selected_ids) or bool(selected_category)
    
    # LLM Analysis of selection vs rest
    if q_clean.startswith(("analyse", "analyze", "analysis", "analyse selection", "analyze selection", "selection analysis")):
        if selection_exists:
            try:
                packet = build_selection_comparison_packet(
                    base_df=base_dataset,
                    selected_df=selected_dataset,
                    selected_category=selected_category
                )
                llm_analysis = run_llm_selection_analysis(llm, packet)
                return jsonify({"response": llm_analysis, "selection_analysis": packet})
            except Exception as e:
                logger.exception("selection_analysis failed: %s", e)
                return jsonify({"response": f"Selection analysis failed: {str(e)}"}), 500
        else:
            return jsonify({
                "response": "There is no active selection to analyse. Select part of a chart first."
            })
    elif q_clean.startswith(("list columns", "list column names", "show columns", "column names")):
        # If the user is asking for columns, simply list them
        # Filter out internal columns and format names (lowercase, no underscores)
        visible_cols = [col.replace("_", " ").replace("-", " ").lower() for col in cols if not col.startswith("_")]
        return jsonify({"response": f"Columns in your dataset: {', '.join(visible_cols)}"})
    else:
        # Otherwise, attempt to parse the query for operations / charts
        spec = parse_query(q, cols, llm=llm)
        if not spec:
            return jsonify({"response": "Could not understand the query."})
        
        operation = spec.get("operation")
        col = spec.get("col")
        
        # Attempt direct nlp handling first
        if operation == "avg" and col:
            return jsonify({"result": round(float(pd.to_numeric(selected_dataset[col], errors="coerce").mean()), 2)})
        if operation == "sum" and col:
            return jsonify({"result": round(float(pd.to_numeric(selected_dataset[col], errors="coerce").sum()), 2)})
        if operation == "max" and col:
            return jsonify({"result": round(float(pd.to_numeric(selected_dataset[col], errors="coerce").max()), 2)})
        if operation == "min" and col:
            return jsonify({"result": round(float(pd.to_numeric(selected_dataset[col], errors="coerce").min()), 2)})
        if operation == "count":
            return jsonify({"result": int(len(selected_dataset))})
        if operation == "list" and col:
            return jsonify({"values": selected_dataset[col].head(50).tolist()})

    # Chart generation
    if operation == "chart":
        chart_spec = spec.get("chart", {})

        if not chart_spec or not chart_spec.get("type"):
            return jsonify({"response": "Please specify chart type"})
                
        try:
            logger.info(f"Generating chart with spec: {chart_spec}")
            chart = render_chart(selected_dataset, chart_spec)
            return jsonify({"chart": chart.to_json(), "message": "Chart generated successfully."})
        except Exception as e:
            logger.exception("Error generating chart: %s", e)
        
    return jsonify({"response": "Could not understand"})

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)