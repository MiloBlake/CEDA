from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_cpp import Llama
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

llm = Llama(model_path="./llm/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

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
        print(f"Upload error: {str(e)}")  # This will show in terminal
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# QUERY
@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_query = data.get("query", "")

    context = ""
    if dataset is not None:
        cols = ", ".join(list(dataset.columns))
        context = f"The dataset has columns: {cols}.\n"

    result = llm(f"{context}Q: {user_query}\nA:", max_tokens=100)
    text = result["choices"][0]["text"].strip()

    return jsonify({"response": text})

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)