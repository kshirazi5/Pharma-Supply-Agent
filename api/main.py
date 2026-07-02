"""
api/main.py
===========
FastAPI application entry point.
Handles CSV file upload, runs the multi-agent pipeline, and serves
the dashboard API endpoints.
"""
from __future__ import annotations
import os
import tempfile
import json
import traceback

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.auth       import router as auth_router, get_current_user
from api.approvals  import router as approvals_router

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Pharma Supply Intelligence API",
    description="Multi-agent pharmaceutical procurement system powered by Google ADK.",
    version="3.0.0",
)

allowed_origin = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(approvals_router)


@app.get("/")
def health():
    return {"status": "ok", "service": "Pharma Supply Intelligence API v3"}


@app.post("/api/run-pipeline")
async def run_pipeline(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a pharmaceutical sales CSV and run the full supply-chain pipeline.

    Runs the tool functions directly (no ADK LLM needed) and returns a
    structured JSON result that the frontend renders.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    # Save upload to a temp file
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        budget = float(os.environ.get("PROCUREMENT_BUDGET", 50000))
        threshold = float(os.environ.get("APPROVAL_THRESHOLD", 10000))

        # ── Step 1: Data Agent — validate & engineer features ──────────────
        from tools.data_tools import validate_and_engineer
        feat_json = validate_and_engineer(tmp_path)
        feat = json.loads(feat_json)
        if not feat.get("ok"):
            raise HTTPException(status_code=422, detail=f"Data validation failed: {feat.get('error')}")

        # ── Step 2: Forecast Agent — run ML models ─────────────────────────
        from tools.forecast_tools import run_forecast
        fc_json = run_forecast(feat_json)
        fc = json.loads(fc_json)

        # ── Step 3: Risk Agent — score risk ────────────────────────────────
        from tools.risk_tools import score_risk, optimise_orders
        rs_json = score_risk(fc_json)
        rs = json.loads(rs_json)

        # ── Step 4: Risk Agent — optimise orders ───────────────────────────
        op_json = optimise_orders(fc_json, budget=budget)
        op = json.loads(op_json)

        # ── Step 5: Risk Agent — anomaly detection ─────────────────────────
        from tools.anomaly_tools import detect_all_anomalies
        an_json = detect_all_anomalies(tmp_path)
        an = json.loads(an_json)

        # ── Step 6: Approval gate ──────────────────────────────────────────
        from tools.approval_tools import check_approval_required
        ap_json = check_approval_required(op_json, threshold=threshold)
        ap = json.loads(ap_json)

        # ── Step 7: Log decisions to Supabase ─────────────────────────────
        from tools.memory_tools import log_decision
        order_plan = op.get("order_plan", {})
        forecasts  = fc.get("forecasts", {})
        anomalies  = an.get("details", {})

        for drug, details in order_plan.items():
            drug_fc  = forecasts.get(drug, {})
            drug_an  = anomalies.get(drug, {})
            status   = "pending" if (ap.get("requires_approval") and
                                     drug in ap.get("flagged_drugs", [])) else "executed"
            try:
                log_decision(
                    drug_col        = drug,
                    units           = details.get("units", 0),
                    predicted_surge = bool(drug_fc.get("surge_flag", False)),
                    confidence      = float(drug_fc.get("surge_prob", 0)),
                    anomaly         = bool(drug_an.get("anomaly", False)),
                    reasoning       = f"Ensemble vol={drug_fc.get('ensemble_volume',0):.2f}, "
                                      f"risk={json.loads(rs_json).get('risk_scores',{}).get(drug,0):.1f}",
                    status          = status,
                )
            except Exception:
                pass  # Don't fail pipeline if logging fails

        # ── Step 8: Slack alert ────────────────────────────────────────────
        try:
            from tools.alert_tools import post_decision_summary, post_approval_request
            if ap.get("requires_approval"):
                post_approval_request(ap_json)
            else:
                post_decision_summary(op_json, rs_json)
        except Exception:
            pass  # Slack is optional

        # ── Build human-readable summary ───────────────────────────────────
        lines = [
            f"Pipeline completed for {feat.get('latest_date')} ({feat.get('rows')} rows)\n",
            f"Budget: ${budget:,.0f} | Threshold: ${threshold:,.0f}\n",
            "=" * 50,
        ]

        risk_scores = rs.get("risk_scores", {})
        for drug, details in order_plan.items():
            drug_fc  = forecasts.get(drug, {})
            risk     = risk_scores.get(drug, 0)
            anom     = anomalies.get(drug, {}).get("anomaly", False)
            surge    = drug_fc.get("surge_flag", False)
            status   = "PENDING APPROVAL" if (ap.get("requires_approval") and
                                               drug in ap.get("flagged_drugs", [])) else "EXECUTED"
            flag     = " [ANOMALY]" if anom else ""
            surge_s  = " [SURGE]" if surge else ""
            lines.append(
                f"{drug}{surge_s}{flag}: {details['units']:.0f} units "
                f"@ ${details['cost']:.0f} | risk={risk:.1f} | {status}"
            )

        lines.append("=" * 50)
        lines.append(f"Total spend: ${op.get('total_cost', 0):,.0f} / ${budget:,.0f}")

        if ap.get("requires_approval"):
            lines.append(f"APPROVAL REQUIRED for: {ap.get('flagged_drugs', [])}")
            lines.append(f"Approval IDs: {ap.get('approval_ids', [])}")
        else:
            lines.append("All orders auto-executed within budget.")

        if an.get("any_anomaly"):
            flagged = [d for d, v in anomalies.items() if v.get("anomaly")]
            lines.append(f"Anomalies detected in: {flagged}")

        return {
            "ok"      : True,
            "user"    : current_user["username"],
            "file"    : file.filename,
            "response": "\n".join(lines),
            "data": {
                "features" : feat,
                "forecasts": fc.get("forecasts"),
                "risk"     : rs.get("risk_scores"),
                "orders"   : op.get("order_plan"),
                "anomalies": an.get("details"),
                "approval" : ap,
            }
        }

    except HTTPException:
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{exc}\n\n{tb}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.get("/api/budget")
def get_budget(current_user: dict = Depends(get_current_user)):
    """Return the configured procurement budget."""
    return {
        "budget"   : float(os.environ.get("PROCUREMENT_BUDGET", 50000)),
        "threshold": float(os.environ.get("APPROVAL_THRESHOLD", 10000)),
    }
