"""
ml/train.py
===========
Train XGBoost (volume forecasting) + Logistic Regression (surge classification)
for each of the 8 ATC drug categories in salesdaily.csv.

Run:
    python -m ml.train
"""
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

DRUG_COLS = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "salesdaily.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_features(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, pd.Series]:
    """Engineer lag / rolling features for a single drug column."""
    df = df.copy()
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.sort_values("datum").reset_index(drop=True)

    df["dayofweek"] = df["datum"].dt.dayofweek
    df["month"] = df["datum"].dt.month
    df["year"] = df["datum"].dt.year
    df["dayofyear"] = df["datum"].dt.dayofyear

    for lag in [1, 2, 3, 7, 14]:
        df[f"lag_{lag}"] = df[col].shift(lag)

    df["rolling_7_mean"] = df[col].shift(1).rolling(7).mean()
    df["rolling_14_std"] = df[col].shift(1).rolling(14).std()
    df = df.dropna()

    feature_cols = [
        "dayofweek", "month", "year", "dayofyear",
        "lag_1", "lag_2", "lag_3", "lag_7", "lag_14",
        "rolling_7_mean", "rolling_14_std",
    ]
    X = df[feature_cols]
    y = df[col]
    return X, y


def build_surge_labels(y: pd.Series, threshold_pct: float = 0.75) -> pd.Series:
    """Label days above the 75th-percentile as surge days (1), others 0."""
    return (y >= y.quantile(threshold_pct)).astype(int)


def train(data_path: str = DATA_PATH):
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path}")

    for col in DRUG_COLS:
        print(f"\n>> Training models for {col}")
        X, y = build_features(df, col)

        # ── XGBoost regressor ──────────────────────────────────────────────
        xgb = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        xgb.fit(X, y)
        joblib.dump(xgb, os.path.join(MODEL_DIR, f"{col}_xgb.pkl"))
        print(f"  XGBoost saved -> {col}_xgb.pkl")

        # ── Random Forest regressor (ensemble backup) ──────────────────────
        rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
        rf.fit(X, y)
        joblib.dump(rf, os.path.join(MODEL_DIR, f"{col}_rf.pkl"))
        print(f"  RandomForest saved -> {col}_rf.pkl")

        # ── Logistic Regression surge classifier ───────────────────────────
        y_surge = build_surge_labels(y)
        lr_pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)),
        ])
        lr_pipe.fit(X, y_surge)
        joblib.dump(lr_pipe, os.path.join(MODEL_DIR, f"{col}_surge_lr.pkl"))
        print(f"  SurgeClassifier saved -> {col}_surge_lr.pkl")

        # ── Save feature column list for inference ─────────────────────────
        joblib.dump(list(X.columns), os.path.join(MODEL_DIR, f"{col}_feature_cols.pkl"))

    print("\nAll models trained and saved to", MODEL_DIR)


if __name__ == "__main__":
    train()
