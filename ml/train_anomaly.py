"""
ml/train_anomaly.py
===================
Train an IsolationForest anomaly-detection model for each drug category
based on weekly-aggregated historical sales.

Run:
    python -m ml.train_anomaly
"""
import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

DRUG_COLS = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "salesdaily.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_weekly_features(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Aggregate daily sales into weekly windows and engineer statistical features."""
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
    weekly["std"] = weekly["std"].fillna(0)
    weekly["range"] = weekly["max"] - weekly["min"]

    # Rolling lag features for anomaly context
    for lag in [1, 2, 4]:
        weekly[f"sum_lag_{lag}"] = weekly["sum"].shift(lag)
    weekly = weekly.dropna()

    feature_cols = ["sum", "mean", "std", "max", "min", "range",
                    "sum_lag_1", "sum_lag_2", "sum_lag_4"]
    return weekly[feature_cols]


def train(data_path: str = DATA_PATH):
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path}")

    for col in DRUG_COLS:
        print(f"\n>> Training IsolationForest for {col}")
        X = build_weekly_features(df, col)

        iso = IsolationForest(
            n_estimators=200,
            contamination=0.05,  # expect ~5% anomaly rate
            random_state=42,
        )
        iso.fit(X)
        joblib.dump(iso, os.path.join(MODEL_DIR, f"{col}_anomaly_iso.pkl"))
        print(f"  IsolationForest saved -> {col}_anomaly_iso.pkl")

    print("\nAll anomaly models saved to", MODEL_DIR)


if __name__ == "__main__":
    train()
