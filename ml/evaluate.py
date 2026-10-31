"""
ml/evaluate.py
==============
Hold-out evaluation for the forecast and surge models, compared with naive baselines.

Trains on everything except the final 365 days and scores one-day-ahead forecasts
on that final year. Uses the same features and hyperparameters as ml/train.py.

Run:
    python -m ml.evaluate
"""
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from ml.train import DATA_PATH, DRUG_COLS, build_features

TEST_DAYS = 365
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def wape(y, p):
    """Weighted absolute percentage error: total absolute error / total actual volume."""
    return np.abs(y - p).sum() / np.abs(y).sum()


def regression_scores(name, y, p):
    return {"model": name, "MAE": np.mean(np.abs(y - p)),
            "RMSE": np.sqrt(np.mean((y - p) ** 2)), "WAPE": wape(y, p)}


def evaluate(data_path=DATA_PATH):
    df = pd.read_csv(data_path)
    reg_rows, surge_rows = [], []

    for col in DRUG_COLS:
        X, y = build_features(df, col)
        X_tr, X_te = X.iloc[:-TEST_DAYS], X.iloc[-TEST_DAYS:]
        y_tr, y_te = y.iloc[:-TEST_DAYS], y.iloc[-TEST_DAYS:]

        xgb = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8,
                           colsample_bytree=0.8, random_state=42, verbosity=0).fit(X_tr, y_tr)
        rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1).fit(X_tr, y_tr)
        p_xgb, p_rf = xgb.predict(X_te), rf.predict(X_te)

        preds = {
            "Naive (yesterday)": X_te["lag_1"].values,
            "Seasonal naive (same day last week)": X_te["lag_7"].values,
            "7-day moving average": X_te["rolling_7_mean"].values,
            "XGBoost": p_xgb,
            "Random Forest": p_rf,
            "Ensemble (XGB + RF average, used by the app)": (p_xgb + p_rf) / 2,
        }
        for name, p in preds.items():
            reg_rows.append({"drug": col, **regression_scores(name, y_te.values, p)})

        # Surge classifier: threshold from training data only, so the test year stays unseen
        thr = y_tr.quantile(0.75)
        s_tr, s_te = (y_tr >= thr).astype(int), (y_te >= thr).astype(int)
        lr = Pipeline([("scaler", StandardScaler()),
                       ("lr", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42))]).fit(X_tr, s_tr)
        prob = lr.predict_proba(X_te)[:, 1]
        if s_te.nunique() == 2:
            surge_rows.append({
                "drug": col, "test_surge_rate": s_te.mean(),
                "ROC-AUC": roc_auc_score(s_te, prob),
                "F1": f1_score(s_te, prob >= 0.5),
                "F1 baseline (surge if 7-day avg above threshold)": f1_score(s_te, X_te["rolling_7_mean"] >= thr),
            })

    reg = pd.DataFrame(reg_rows)
    surge = pd.DataFrame(surge_rows).set_index("drug").round(3)

    # Pool across drugs: WAPE weights each category by volume, so report the total
    overall = (reg.assign(abs_err=reg["MAE"] * TEST_DAYS)
                  .groupby("model", sort=False)
                  .agg(MAE=("MAE", "mean"), RMSE=("RMSE", "mean")))
    totals = {}
    for col in DRUG_COLS:
        _, y = build_features(df, col)
        totals[col] = y.iloc[-TEST_DAYS:].abs().sum()
    reg["abs_err_total"] = reg["MAE"] * TEST_DAYS
    overall["WAPE (pooled)"] = (reg.groupby("model", sort=False)["abs_err_total"].sum()
                                / sum(totals.values()))
    overall = overall.round(3).sort_values("WAPE (pooled)")

    per_drug = (reg.pivot(index="drug", columns="model", values="WAPE")
                   [["Seasonal naive (same day last week)", "7-day moving average",
                     "Ensemble (XGB + RF average, used by the app)"]]
                   .round(3))

    print("\n=== Forecast accuracy, final 365 days (averaged over 8 drug categories) ===")
    print(overall.to_string())
    print("\n=== WAPE by drug category ===")
    print(per_drug.to_string())
    print("\n=== Surge classifier, final 365 days ===")
    print(surge.to_string())

    os.makedirs(OUT_DIR, exist_ok=True)
    overall.to_csv(os.path.join(OUT_DIR, "forecast_overall.csv"))
    per_drug.to_csv(os.path.join(OUT_DIR, "forecast_wape_by_drug.csv"))
    surge.to_csv(os.path.join(OUT_DIR, "surge_classifier.csv"))
    print(f"\nSaved tables to {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    evaluate()
