"""
tools/memory_tools.py
=====================
Recall past ordering decisions from Supabase and log new ones.
This gives the Risk Agent adaptive memory across runs.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

from db.supabase_client import get_client


def recall_past_decisions(drug_col: str, lookback: int = 10) -> str:
    """
    Retrieve the last `lookback` decisions for a specific drug category.
    Used to temper confidence if the drug was previously over-ordered or
    caused a false-positive surge alert.

    Args:
        drug_col: One of the 8 ATC drug category codes.
        lookback: Number of most-recent decisions to retrieve.

    Returns:
        JSON string with list of past decisions and summary stats.
    """
    try:
        client = get_client()
        resp = (
            client.table("decisions")
            .select("*")
            .eq("drug_col", drug_col)
            .order("created_at", desc=True)
            .limit(lookback)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return json.dumps({"ok": True, "drug_col": drug_col, "records": [],
                               "false_surge_rate": 0.0, "avg_confidence": 0.0})

        # Compute summary metrics for the agent
        total          = len(rows)
        false_surges   = sum(1 for r in rows if r.get("predicted_surge") and
                             r.get("status") == "rejected")
        avg_confidence = sum(r.get("confidence", 0) for r in rows) / total

        return json.dumps({
            "ok"              : True,
            "drug_col"        : drug_col,
            "records"         : rows,
            "false_surge_rate": round(false_surges / total, 3),
            "avg_confidence"  : round(avg_confidence, 3),
        })
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def log_decision(
    drug_col: str,
    units: float,
    predicted_surge: bool,
    confidence: float,
    anomaly: bool,
    reasoning: str,
    status: str = "executed",
) -> str:
    """
    Persist an ordering decision to Supabase.

    Args:
        drug_col        : ATC category code.
        units           : Units to order.
        predicted_surge : Whether the model flagged a demand surge.
        confidence      : Surge probability (0–1).
        anomaly         : Whether IsolationForest flagged an anomaly.
        reasoning       : Free-text reasoning from the agent.
        status          : 'executed', 'pending', or 'rejected'.

    Returns:
        JSON string with the inserted row or an error.
    """
    try:
        client = get_client()
        payload = {
            "drug_col"        : drug_col,
            "units_ordered"   : units,
            "predicted_surge" : predicted_surge,
            "confidence"      : confidence,
            "anomaly_detected": anomaly,
            "reasoning"       : reasoning,
            "status"          : status,
            "created_at"      : datetime.now(timezone.utc).isoformat(),
        }
        resp = client.table("decisions").insert(payload).execute()
        return json.dumps({"ok": True, "inserted": resp.data})
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})
