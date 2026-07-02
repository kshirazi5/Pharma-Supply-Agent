"""
tools/data_tools.py
===================
Validate an uploaded CSV and engineer time-series features
for downstream forecasting and anomaly agents.
"""
from __future__ import annotations
import json
import pandas as pd

REQUIRED_COLS = ["datum", "M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
DRUG_COLS     = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]


def validate_and_engineer(file_path: str) -> str:
    """
    Validate the CSV structure and return a JSON summary of the latest row's
    engineered features for all 8 drug categories.

    Args:
        file_path: Absolute or relative path to the salesdaily CSV.

    Returns:
        JSON string with keys: 'ok', 'rows', 'latest_date', 'features'.
    """
    try:
        df = pd.read_csv(file_path, parse_dates=["datum"])
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Cannot read file: {exc}"})

    # ── Column validation ──────────────────────────────────────────────────────
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        return json.dumps({"ok": False, "error": f"Missing columns: {missing}"})

    df = df.sort_values("datum").reset_index(drop=True)
    features: dict[str, dict] = {}

    for col in DRUG_COLS:
        series = df[col].fillna(0)
        last_val  = float(series.iloc[-1])
        lag1      = float(series.iloc[-2]) if len(series) >= 2 else last_val
        lag7      = float(series.iloc[-8]) if len(series) >= 8 else last_val
        roll7m    = float(series.tail(7).mean())
        roll14std = float(series.tail(14).std()) if len(series) >= 14 else 0.0

        features[col] = {
            "last_value"    : round(last_val, 4),
            "lag_1"         : round(lag1, 4),
            "lag_7"         : round(lag7, 4),
            "rolling_7_mean": round(roll7m, 4),
            "rolling_14_std": round(roll14std, 4),
            "dayofweek"     : int(df["datum"].iloc[-1].dayofweek),
            "month"         : int(df["datum"].iloc[-1].month),
            "year"          : int(df["datum"].iloc[-1].year),
            "dayofyear"     : int(df["datum"].iloc[-1].dayofyear),
        }

    return json.dumps({
        "ok"         : True,
        "rows"       : len(df),
        "latest_date": str(df["datum"].iloc[-1].date()),
        "features"   : features,
    })
