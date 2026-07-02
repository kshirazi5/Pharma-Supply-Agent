"""
tools/approval_tools.py
=======================
Gate high-value orders: auto-execute small orders, hold large ones
in Supabase pending_approvals for human review.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

from db.supabase_client import get_client

UNIT_COST = {"M01AB": 12, "M01AE": 15, "N02BA": 8, "N02BE": 6,
             "N05B": 20, "N05C": 18, "R03": 10, "R06": 9}


def check_approval_required(plan_json: str, threshold: float | None = None) -> str:
    """
    Inspect the optimised order plan and decide if manager approval is needed.

    Rules:
      • If any single-drug cost >= threshold → hold ALL orders for approval.
      • Otherwise auto-execute and mark decisions as 'executed'.

    Args:
        plan_json : JSON string from risk_tools.optimise_orders.
        threshold : Cost threshold in USD. Defaults to env APPROVAL_THRESHOLD.

    Returns:
        JSON with 'requires_approval' bool, 'approval_ids' list (if held),
        and 'auto_executed' list (if executed).
    """
    if threshold is None:
        threshold = float(os.environ.get("APPROVAL_THRESHOLD", 10000))

    data = json.loads(plan_json)
    if not data.get("ok"):
        return json.dumps({"ok": False, "error": "Bad plan input"})

    order_plan = data.get("order_plan", {})
    flagged: list[str] = []
    approval_ids: list[int] = []

    for col, details in order_plan.items():
        cost = details.get("cost", 0)
        if cost >= threshold:
            flagged.append(col)

    requires_approval = bool(flagged)
    client = get_client()

    if requires_approval:
        # Write all flagged items to pending_approvals
        for col in flagged:
            details = order_plan[col]
            payload = {
                "drug_col"      : col,
                "units_ordered" : details.get("units", 0),
                "estimated_cost": details.get("cost", 0),
                "plan_json"     : details,
                "status"        : "pending",
                "created_at"    : datetime.now(timezone.utc).isoformat(),
            }
            resp = client.table("pending_approvals").insert(payload).execute()
            if resp.data:
                approval_ids.append(resp.data[0]["id"])

        return json.dumps({
            "ok"                : True,
            "requires_approval" : True,
            "flagged_drugs"     : flagged,
            "approval_ids"      : approval_ids,
            "message"           : f"Orders for {flagged} held pending manager approval.",
        })
    else:
        return json.dumps({
            "ok"               : True,
            "requires_approval": False,
            "auto_executed"    : list(order_plan.keys()),
            "message"          : "All orders within budget threshold — auto-executed.",
        })
