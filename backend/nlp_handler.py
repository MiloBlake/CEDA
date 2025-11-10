AVG_KEYWORDS = ["average", "mean", "avg", "typical"]
SUM_KEYWORDS = ["sum", "total", "add", "combined"]
MAX_KEYWORDS = ["max", "maximum", "highest", "largest", "biggest"]
MIN_KEYWORDS = ["min", "minimum", "lowest", "smallest", "least"]
COUNT_KEYWORDS = ["count", "how many", "number of"]

def detect_intent(query: str) -> str:
    query_lower = query.lower()
    
    if any(word in query_lower for word in AVG_KEYWORDS):
        return "avg"
    
    elif any(word in query_lower for word in SUM_KEYWORDS):
        return "sum"
    
    elif any(word in query_lower for word in MAX_KEYWORDS):
        return "max"
    
    elif any(word in query_lower for word in MIN_KEYWORDS):
        return "min"
    
    elif any(word in query_lower for word in COUNT_KEYWORDS):
        return "count"
    
    elif any(word in query_lower for word in ["summary", "describe", "stats", "overview"]):
        return "stat_summary"
    
    return "unknown"
