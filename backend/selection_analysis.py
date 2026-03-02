import json
from typing import Any, Dict, Optional

import pandas as pd

Llama = Any

def build_selection_comparison_packet(base_df: pd.DataFrame,
                                      selected_df: pd.DataFrame,
                                      selected_category: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    '''Builds a packet of information for comparing the selected subset of data to the rest of the dataset.'''

    if "_row_id" not in base_df.columns:
        raise ValueError("base_df must include _row_id")

    # Seperate the rest of the data from the selected data
    selected_ids = set(selected_df["_row_id"].tolist()) if len(selected_df) else set()
    rest_df = base_df[~base_df["_row_id"].isin(selected_ids)]

    # If there are no rows in the rest of the dataset
    if len(rest_df) == 0:
        packet["notes"].append("Selection includes all rows; no 'rest' group to compare against.")
        return packet

    n_sel = int(len(selected_df))
    n_total = int(len(base_df))
    pct = round((n_sel / n_total) * 100, 2) if n_total else 0.0

    packet: Dict[str, Any] = {
        "selection": {
            "n_selected": n_sel,
            "n_total": n_total,
            "selected_pct": pct,
            "basis": selected_category or None
        },
        "rest": {"n_rest": int(len(rest_df))},
        "top_numeric_mean_differences": [],
        "notes": []
    }

    if n_sel == 0:
        packet["notes"].append("No rows are selected; cannot compare selection vs rest.")
        return packet

    # Compare selected vs rest - ignore non-numeric columns 
    diffs = []
    for col in base_df.columns:
        if col.lower().endswith("id"):
            continue

        sel_num = pd.to_numeric(selected_df[col], errors="coerce").dropna()
        rest_num = pd.to_numeric(rest_df[col], errors="coerce").dropna()

        if len(sel_num) < 1 or len(rest_num) < 1:
            continue

        sel_mean = float(sel_num.mean())
        rest_mean = float(rest_num.mean())
        delta = sel_mean - rest_mean

        diffs.append({
            "col": col,
            "selected_mean": round(sel_mean, 4),
            "rest_mean": round(rest_mean, 4),
            "delta_mean": round(delta, 4),
            "n_selected_numeric": int(len(sel_num)),
            "n_rest_numeric": int(len(rest_num))
        })

    if not diffs:
        packet["notes"].append("No numeric columns found.")
        return packet

    # Sort by mean difference and take top 3
    diffs.sort(key=lambda x: abs(float(x["delta_mean"])), reverse=True)
    packet["top_numeric_mean_differences"] = diffs[:3]
    return packet

def run_llm_selection_analysis(llm: Optional[Any], packet: Dict[str, Any]) -> str:
    if llm is None:
        sel = packet["selection"]
        lines = [f"Selection: {sel['n_selected']} / {sel['n_total']} rows ({sel['selected_pct']}%)."]
        for item in packet.get("top_numeric_mean_differences", []):
            lines.append(f"- {item['col']}: mean {item['selected_mean']} vs {item['rest_mean']} (Δ {item['delta_mean']})")
        return "\n".join(lines)

    compact_packet = {
    "selection": packet["selection"],
    "rest": packet["rest"],
    "top_numeric_mean_differences": packet["top_numeric_mean_differences"]
    }

    prompt = f"""
You are given computed numeric differences for a selected subset vs the rest.

TASK:
- Choose and discuss some findings from the data (do not invent new metrics)
- Write a 1–2 sentence interpretation based on the findings (stay conservative - no causal claims)

Output JSON only with key_findings and interpretation as single strings:
{{
  "key_findings": "...",
  "interpretation": "..."
}}

Data:
{json.dumps(compact_packet, ensure_ascii=False, default=str)}
""".strip()
    
    resp = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "You analyse data using only the JSON provided."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.05,
        max_tokens=600,
        top_p = 0.85
    )

    # Parse and return the response
    response_text = resp["choices"][0]["message"]["content"].strip()
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        return "Error: Invalid JSON response from LLM"
    
    findings = parsed.get("key_findings")
    if isinstance(findings, list):
        findings = "\n".join(findings)
    findings = findings or "No findings extracted"
    
    interpretation = parsed.get("interpretation") or "No interpretation available"
    analysis = f"{findings}\n\n{interpretation}"
    return analysis
