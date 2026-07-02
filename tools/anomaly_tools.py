"""
tools/anomaly_tools.py
======================
Detect anomalous sales spikes using the trained IsolationForest models.
"""
from __future__ import annotations
import json
import os
import joblib
import pandas as pd
import numpy as np

DRUG_COLS = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")


def _build_latest_weekly_features(df: pd.DataFrame, col: str) -> np.ndarray:
    """Aggregate the most-recent full week's data into the same feature vector
    used during training."""
    df = df.copy()
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.sort_values("datum").reset_index(drop=True)
    df["week"] = df["datum"].dt.isocalendar().week.astype(int)
    df["year"] = df["datum"].dt.year

    weekly = (
        df.groupby(["year", "week"])[col]
        .agg(["sum", "mean", "std", "max", "min"])
        .reset_index()
    )
    weekly.columns = ["year", "week", "sum", "mean", "std", "max", "min"]
    weekly["std"]   = weekly["std"].fillna(0)
    weekly["range"] = weekly["max"] - weekly["min"]

    for lag in [1, 2, 4]:
        weekly[f"sum_lag_{lag}"] = weekly["sum"].shift(lag)
    weekly = weekly.dropna()

    if weekly.empty:
        return None

    feature_cols = ["sum", "mean", "std", "max", "min", "range",
                    "sum_lag_1", "sum_lag_2", "sum_lag_4"]
    latest = weekly[feature_cols].iloc[[-1]].values
    return latest


def detect_anomaly(file_path: str, drug_col: str) -> str:
    """
    Run IsolationForest to check whether the current week's sales
    for `drug_col` represent an abnormal spike.

    Args:
        file_path : Path to the sales CSV.
        drug_col  : One of the 8 ATC codes.

    Returns:
        JSON string with 'anomaly' bool and 'anomaly_score' float.
    """
    try:
        model_path = os.path.join(MODEL_DIR, f"{drug_col}_anomaly_iso.pkl")
        if not os.path.exists(model_path):
            return json.dumps({
                "ok": False,
                "error": f"Anomaly model not found for {drug_col}. Run ml/train_anomaly.py first."
            })

        iso = joblib.load(model_path)
        df  = pd.read_csv(file_path)
        vec = _build_latest_weekly_features(df, drug_col)

        if vec is None:
            return json.dumps({"ok": True, "drug_col": drug_col,
                               "anomaly": False, "anomaly_score": 0.0,
                               "note": "Not enough data for weekly aggregation."})

        # IsolationForest: -1 = anomaly, 1 = normal
        pred  = iso.predict(vec)[0]
        score = float(iso.score_samples(vec)[0])  # more negative = more anomalous

        return json.dumps({
            "ok"           : True,
            "drug_col"     : drug_col,
            "anomaly"      : bool(pred == -1),
            "anomaly_score": round(score, 4),
        })
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def detect_all_anomalies(file_path: str) -> str:
    """Run detect_anomaly for all 8 drug categories and return a combined report."""
    results: dict = {}
    for col in DRUG_COLS:
        result = json.loads(detect_anomaly(file_path, col))
        results[col] = result
    any_anomaly = any(v.get("anomaly") for v in results.values())
    return json.dumps({"ok": True, "any_anomaly": any_anomaly, "details": results})
