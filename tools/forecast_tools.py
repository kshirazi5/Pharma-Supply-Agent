"""
tools/forecast_tools.py
=======================
Load trained ML models and produce volume forecasts + surge probabilities
for each ATC drug category.
"""
from __future__ import annotations
import json
import os
import joblib
import numpy as np

DRUG_COLS = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")


def _load(name: str):
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}. Run ml/train.py first.")
    return joblib.load(path)


def run_forecast(features_json: str) -> str:
    """
    Given a JSON string produced by data_tools.validate_and_engineer,
    run XGBoost + LR models and return predictions.

    Args:
        features_json: JSON string with key 'features' mapping drug → feature dict.

    Returns:
        JSON string with keys per drug: 'xgb_volume', 'rf_volume', 'surge_prob', 'surge_flag'.
    """
    data = json.loads(features_json)
    if not data.get("ok"):
        return json.dumps({"ok": False, "error": data.get("error", "Bad feature input")})

    raw_features = data["features"]
    results: dict = {}

    feature_order = [
        "dayofweek", "month", "year", "dayofyear",
        "lag_1", "lag_2", "lag_3", "lag_7", "lag_14",
        "rolling_7_mean", "rolling_14_std",
    ]

    for col in DRUG_COLS:
        feats = raw_features.get(col, {})

        # Build feature vector — lag_2/lag_3/lag_14 may be missing from live input;
        # fall back to lag_1 value gracefully.
        vec = np.array([[
            feats.get("dayofweek", 0),
            feats.get("month", 1),
            feats.get("year", 2024),
            feats.get("dayofyear", 1),
            feats.get("lag_1", feats.get("last_value", 0)),
            feats.get("lag_2", feats.get("lag_1", 0)),
            feats.get("lag_3", feats.get("lag_1", 0)),
            feats.get("lag_7", feats.get("last_value", 0)),
            feats.get("lag_14", feats.get("last_value", 0)),
            feats.get("rolling_7_mean", feats.get("last_value", 0)),
            feats.get("rolling_14_std", 0),
        ]])

        try:
            xgb  = _load(f"{col}_xgb.pkl")
            rf   = _load(f"{col}_rf.pkl")
            lr   = _load(f"{col}_surge_lr.pkl")

            xgb_vol  = float(xgb.predict(vec)[0])
            rf_vol   = float(rf.predict(vec)[0])
            surge_p  = float(lr.predict_proba(vec)[0][1])
            ensemble = round((xgb_vol + rf_vol) / 2, 4)

            results[col] = {
                "xgb_volume" : round(xgb_vol, 4),
                "rf_volume"  : round(rf_vol, 4),
                "ensemble_volume": ensemble,
                "surge_prob" : round(surge_p, 4),
                "surge_flag" : bool(surge_p >= 0.5),
            }
        except FileNotFoundError as e:
            results[col] = {"error": str(e)}

    return json.dumps({"ok": True, "forecasts": results})
