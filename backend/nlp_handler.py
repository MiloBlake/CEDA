import re
from difflib import SequenceMatcher

AVG_KEYWORDS = ["average", "mean", "avg", "typical"]
SUM_KEYWORDS = ["sum", "total", "add", "combined"]
MAX_KEYWORDS = ["max", "maximum", "highest", "largest", "biggest"]
MIN_KEYWORDS = ["min", "minimum", "lowest", "smallest", "least"]
COUNT_KEYWORDS = ["count", "how many", "number of"]

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
    if any(w in q for w in ["summary", "describe", "stats", "overview"]): return "stat_summary"
    return "unknown"
