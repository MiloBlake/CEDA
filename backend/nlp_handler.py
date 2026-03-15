import json
import re
from difflib import SequenceMatcher
import logging

logger = logging.getLogger("backend.nlp_handler")

AVG_KEYWORDS = ["average", "mean", "avg"]
SUM_KEYWORDS = ["sum", "total", "add", "combined"]
MAX_KEYWORDS = ["max", "maximum", "highest", "largest", "biggest"]
MIN_KEYWORDS = ["min", "minimum", "lowest", "smallest", "least"]
COUNT_KEYWORDS = ["count", "how many", "number of"]
LIST_KEYWORDS = ["list"]

CHART_KEYWORDS = [
    "chart", "graph", "plot", "visualize", "visualise", 
    "visualization", "visualisation", "display",
    "bar chart", "bar graph", "histogram", "bar",
    "line chart", "line graph", "line",
    "scatter plot", "scatter graph", "scatter",
    "pie chart", "pie graph", "pie",
    "box plot", "boxplot", "box",
    "distribution", "correlation", "relationship"
]

def normalise_text(text: str) -> str:
    # Make text lowercase and remove special characters
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
    
def _fuzzy_has(tokens, keywords, thresh=0.80):
    # Check if any token matches any keyword with fuzzy matching
    for t in tokens:
        for k in keywords:
            if k in t:
                return True
            if SequenceMatcher(None, t, k).ratio() >= thresh:
                return True
    return False

def detect_intent(query: str) -> str:
    q = normalise_text(query)
    tokens = re.findall(r"[a-z]+", q)
    if _fuzzy_has(tokens, CHART_KEYWORDS): return "chart"
    if _fuzzy_has(tokens, AVG_KEYWORDS): return "avg"
    if _fuzzy_has(tokens, SUM_KEYWORDS): return "sum"
    if _fuzzy_has(tokens, MAX_KEYWORDS): return "max"
    if _fuzzy_has(tokens, MIN_KEYWORDS): return "min"
    if _fuzzy_has(tokens, COUNT_KEYWORDS): return "count"
    if _fuzzy_has(tokens, LIST_KEYWORDS): return "list"
    if any(w in q for w in ["summary", "describe", "stats", "overview"]): return "stat_summary"
    return "unknown"


def detect_chart_type(query: str) -> str:
    q = normalise_text(query)
    
    if "scatter" in q or "correlation" in q or "relationship" in q:
        return "scatter"

    if "boxplot" in q or "box plot" in q or "box" in q:
        return "box"

    if "histogram" in q or "distribution" in q:
        return "histogram"

    if "bar chart" in q or "bar graph" in q or "bar" in q:
        return "bar"

    if "line chart" in q or "line graph" in q or "line" in q:
        return "line"

    if "pie chart" in q or "pie graph" in q or "pie" in q:
        return "pie"
    
    if any(w in q for w in ["chart", "graph", "plot", "visualize", "display"]):
        return None
    
    return None


def detect_columns(query: str, available_columns: list[str], max_cols: int = 3) -> list[str]:
    # Find columns mentioned in the query using fuzzy matching
    query_norm = normalise_text(query)
    q_tokens = set(re.findall(r"[a-z0-9]+", query_norm))

    matched_columns: list[str] = []
    matched_columns_positions: list[tuple[int, str]] = []

    # To avoid duplicates in query, ie "show me the distribution of age in employee ages"
    seen = set()

    for col in available_columns:
        col_norm = normalise_text(col)
        if not col_norm:
            continue    
        
        # if multiple words in column name
        if " " in col_norm:
            idx = query_norm.find(col_norm)
            if idx != -1:
                matched_columns_positions.append((idx, col))

        # if single word in column name
        else:
            if col_norm in q_tokens:
                idx = query_norm.find(col_norm)
                matched_columns_positions.append((idx, col))

    matched_columns_positions.sort(key=lambda x: x[0])

    for _, col in matched_columns_positions:
        if col not in seen:
            matched_columns.append(col)
            seen.add(col)
        if len(matched_columns) >= max_cols:
            break

    return matched_columns


def parse_query(query: str, columns: list[str], llm=None) -> dict | None:
    '''
        {
        "operation": "avg|sum|min|max|count|list|chart",
        "col": "<column(s) or None>",
        "chart": {"type": "...", "x": "...", "y": "...", "group": "...", "agg": "..."} or None,
        "raw": "<original query>"
        }
    '''
    q = normalise_text(query) 
    intent = detect_intent(query)
    mentioned = detect_columns(query, columns, max_cols=2)

    if intent in {"avg", "sum", "min", "max", "list"}:
        col = mentioned[0] if mentioned else None
        if col:
            return { "operation": intent, "col": col, "chart": None, "raw": query }
        else:
            return llm_query_parser_fallback(query, columns, llm) if llm else None
        
    if intent == "count":
        return { "operation": intent, "col": None, "chart": None, "raw": query }
    
    if intent == "chart":
        chart_type = detect_chart_type(query)

        x_col = mentioned[0] if len(mentioned) >= 1 else None
        y_col = mentioned[1] if len(mentioned) >= 2 else None

        if chart_type in {"histogram", "box", "pie"}:
            y_col = None
    
        agg = None

        if any(w in q for w in ["average", "mean", "avg"]):
            agg = "mean"
        elif any(w in q for w in ["sum", "total"]):
            agg = "sum"
        elif any(w in q for w in ["count", "how many", "number of"]):
            agg = "count"

        if y_col and ((" by " in q) or (" vs " in q) or (" versus " in q)):
            if agg is None:
                agg = "mean"

        spec = {
            "operation": "chart",
            "col": None,
            "chart": {
                "type": chart_type,
                "x": x_col,
                "y": y_col,
                "group": None,
                "agg": agg or "count"
            },
            "raw": query
        }
        return spec
    
    if llm:
        return llm_query_parser_fallback(query, columns, llm)
    
    return None

def llm_query_parser_fallback(query: str, columns: list[str], llm) -> dict | None:
    """
    Fallback method to parse the query using an LLM if the rule-based parsing fails. 
    The LLM is prompted to return a JSON with the proper structure.
    """
    if not llm:
        return None

    prompt = (
        "You are a JSON API. Return ONLY valid JSON, nothing else.\n"
        f"Columns: {', '.join(columns)}\n"
        'Schema: {"operation":"avg|sum|max|min|count|list","column":"<column name or null>"}\n'
        'Example 1: {"operation":"avg","column":"Age"}\n'
        'Example 2: {"operation":"count","column":null}\n'
        f"User: {query}\n"
    )

    # Validate LLM response structure
    try:
        resp = llm(prompt, max_tokens=200, temperature=0.0, top_p=1.0)
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return None
    
    # Check response structure
    if not resp or not isinstance(resp, dict):
        logger.warning("LLM response is not a dict")
        return None
    
    if "choices" not in resp or not resp["choices"]:
        logger.warning("LLM response missing 'choices' or choices is empty")
        return None
    
    # Extract text from response
    first_choice = resp["choices"][0]
    if not isinstance(first_choice, dict):
        logger.warning("Choice is not a dict")
        return None

    text = (
        first_choice.get("text", "") or 
        first_choice.get("message", {}).get("content", "")
    ).strip()

    if not text:
        logger.warning("LLM response has no text content")
        return None

    # Extract JSON from text
    m = re.search(r"\{[^{}]*\}", text)
    if not m:
        logger.warning(f"No JSON found in LLM response: {text[:100]}")
        return None
        
    # Parse JSON
    try:
        parsed = json.loads(m.group())
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from LLM response: {e}")
        return None

    # Validate parsed object structure
    if not isinstance(parsed, dict):
        logger.warning("Parsed JSON is not a dict")
        return None
    
    operation = parsed.get("operation")
    col = parsed.get("column")

    # Validate operation
    valid_operations = {"avg", "sum", "max", "min", "list", "count"}
    if operation not in valid_operations:
        logger.warning(f"Invalid operation: {operation}")
        return None

    # Validate column
    if operation in {"avg", "sum", "max", "min", "list"}:
        if not col or col not in columns:
            logger.warning(f"Invalid or missing column '{col}' for operation '{operation}'")
            return None
        
    reworked_prompt = {"operation": operation, "col": col, "chart": None, "raw": query}
    logger.info(f"LLM query parser fallback returned: {reworked_prompt}")
    return reworked_prompt