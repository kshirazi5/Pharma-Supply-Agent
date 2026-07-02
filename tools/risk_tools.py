"""
tools/risk_tools.py
===================
Score cross-category procurement risk and solve a budget-constrained
order optimisation using a greedy fractional-knapsack heuristic.
"""
from __future__ import annotations
import json
import os

DRUG_COLS   = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
UNIT_COST   = {"M01AB": 12, "M01AE": 15, "N02BA": 8, "N02BE": 6,
               "N05B": 20, "N05C": 18, "R03": 10, "R06": 9}  # USD per unit


def score_risk(forecast_json: str) -> str:
    """
    Compute a composite risk score (0-100) per drug based on surge_prob,
    ensemble_volume, and historical volatility proxy (rolling_14_std).

    Args:
        forecast_json: Output from forecast_tools.run_forecast.

    Returns:
        JSON with 'risk_scores' dict per drug and overall 'max_risk'.
    """
    data = json.loads(forecast_json)
    if not data.get("ok"):
        return json.dumps({"ok": False, "error": "Bad forecast input"})

    forecasts = data["forecasts"]
    risk_scores: dict[str, float] = {}

    for col in DRUG_COLS:
        fc = forecasts.get(col, {})
        if "error" in fc:
            risk_scores[col] = 0.0
            continue
        surge_p  = fc.get("surge_prob", 0)
        vol      = fc.get("ensemble_volume", 0)
        # normalise volume contribution using empirical max (rough constant)
        vol_norm = min(vol / 200.0, 1.0)
        score    = round((0.60 * surge_p + 0.40 * vol_norm) * 100, 2)
        risk_scores[col] = score

    return json.dumps({
        "ok"         : True,
        "risk_scores": risk_scores,
        "max_risk"   : max(risk_scores.values()) if risk_scores else 0,
    })


def optimise_orders(forecast_json: str, budget: float | None = None) -> str:
    """
    Greedy fractional-knapsack: maximise total risk coverage subject to
    a procurement budget constraint.

    Args:
        forecast_json: Output from forecast_tools.run_forecast.
        budget: Total procurement budget in USD. Defaults to env PROCUREMENT_BUDGET.

    Returns:
        JSON with 'order_plan' dict per drug and 'total_cost'.
    """
    if budget is None:
        budget = float(os.environ.get("PROCUREMENT_BUDGET", 50000))

    data = json.loads(forecast_json)
    if not data.get("ok"):
        return json.dumps({"ok": False, "error": "Bad forecast input"})

    forecasts = data["forecasts"]

    items: list[dict] = []
    for col in DRUG_COLS:
        fc = forecasts.get(col, {})
        if "error" in fc:
            continue
        vol        = max(fc.get("ensemble_volume", 0), 0)
        surge_p    = fc.get("surge_prob", 0)
        # Desired units = ensemble volume × surge multiplier (1.25 if surge)
        desired    = vol * (1.25 if fc.get("surge_flag") else 1.0)
        cost_each  = UNIT_COST.get(col, 10)
        total_cost = desired * cost_each
        value      = surge_p * desired  # value = risk-weighted units

        items.append({
            "col"       : col,
            "desired"   : desired,
            "cost_each" : cost_each,
            "total_cost": total_cost,
            "value"     : value,
        })

    # Sort by value-per-dollar (descending)
    items.sort(key=lambda x: x["value"] / max(x["cost_each"], 1), reverse=True)

    remaining = budget
    order_plan: dict[str, dict] = {}

    for item in items:
        col = item["col"]
        if remaining <= 0:
            order_plan[col] = {"units": 0, "cost": 0}
            continue
        if item["total_cost"] <= remaining:
            units = item["desired"]
            cost  = item["total_cost"]
        else:
            units = remaining / item["cost_each"]
            cost  = remaining
        remaining -= cost
        order_plan[col] = {
            "units"    : round(units, 2),
            "cost"     : round(cost, 2),
            "cost_each": item["cost_each"],
        }

    return json.dumps({
        "ok"         : True,
        "budget"     : budget,
        "total_cost" : round(budget - remaining, 2),
        "remaining"  : round(remaining, 2),
        "order_plan" : order_plan,
    })
