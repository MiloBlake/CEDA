# CEDA – Conversational Exploratory Data Analysis

CEDA is a local, privacy-focused conversational data analysis tool that allows you to query your datasets using natural language. It combines a rule-based NLP parser with an LLM fallback to interpret queries and generate results and visualisations.

---

## Features

* Conversational language queries (average, sum, min, max, count)
* Data visualisation (bar, scatter, line, pie, histogram, box plot)
* LLM fallback for ambiguous queries using Phi-3.5-mini via llama.cpp
* Selection analysis using the `analyse` command
* Fully local execution to ensure data privacy

---

## Architecture

CEDA uses a client-server architecture:

* Frontend: React-based chatbot interface
* Backend: Flask API for query processing
* Components:

  * NLP handler (rule-based)
  * LLM fallback (llama.cpp)
  * Data processing (Pandas)
  * Visualisation (Plotly)

---

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Author

Milo Blake
University of Galway
Final Year Project
