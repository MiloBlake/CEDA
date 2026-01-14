import re
from difflib import SequenceMatcher

AVG_KEYWORDS = ["average", "mean", "avg", "typical"]
SUM_KEYWORDS = ["sum", "total", "add", "combined"]
MAX_KEYWORDS = ["max", "maximum", "highest", "largest", "biggest"]
MIN_KEYWORDS = ["min", "minimum", "lowest", "smallest", "least"]
COUNT_KEYWORDS = ["count", "how many", "number of"]
LIST_KEYWORDS = ["show", "list", "return", "give"]

CHART_KEYWORDS = {
    "bar": ["bar chart", "bar graph", "histogram"],
    "line": ["line chart", "line graph"],
    "scatter": ["scatter plot", "scatter graph"],
    "pie": ["pie chart", "pie graph"],
}

def _fuzzy_has(tokens, keywords, thresh=0.80):
    for t in tokens:
        for k in keywords:
            if k in t:
                return True
            if SequenceMatcher(None, t, k).ratio() >= thresh:
                return True
    return False

def detect_intent(query: str) -> str:
    q = query.lower()
    tokens = re.findall(r"[a-z]+", q)

    if _fuzzy_has(tokens, AVG_KEYWORDS): return "avg"
    if _fuzzy_has(tokens, SUM_KEYWORDS): return "sum"
    if _fuzzy_has(tokens, MAX_KEYWORDS): return "max"
    if _fuzzy_has(tokens, MIN_KEYWORDS): return "min"
    if _fuzzy_has(tokens, COUNT_KEYWORDS): return "count"
    if _fuzzy_has(tokens, LIST_KEYWORDS): return "list"
    if _fuzzy_has(tokens, CHART_KEYWORDS): return "chart"
    if any(w in q for w in ["summary", "describe", "stats", "overview"]): return "stat_summary"
    return "unknown"