"""
tools/alert_tools.py
====================
Post decision summaries and approval-needed notifications to Slack.
"""
from __future__ import annotations
import json
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

_slack_client: WebClient | None = None


def _get_slack() -> WebClient:
    global _slack_client
    if _slack_client is None:
        token = os.environ.get("SLACK_BOT_TOKEN", "")
        _slack_client = WebClient(token=token)
    return _slack_client


def post_decision_summary(order_plan_json: str, risk_json: str) -> str:
    """
    Post a formatted Slack message summarising the executed order plan
    and risk scores for all drug categories.

    Args:
        order_plan_json : JSON string from risk_tools.optimise_orders.
        risk_json       : JSON string from risk_tools.score_risk.

    Returns:
        JSON with 'ok' and Slack 'ts' (message timestamp).
    """
    channel = os.environ.get("SLACK_CHANNEL", "#supply-chain")
    try:
        plan  = json.loads(order_plan_json)
        risks = json.loads(risk_json)
        orders = plan.get("order_plan", {})
        scores = risks.get("risk_scores", {})

        lines = ["*📦 Pharma Supply Intelligence — Order Summary*\n"]
        for col, details in orders.items():
            risk  = scores.get(col, 0)
            units = details.get("units", 0)
            cost  = details.get("cost", 0)
            emoji = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
            lines.append(f"{emoji} *{col}* — {units:.0f} units @ ${cost:.0f} | risk: {risk:.1f}")

        lines.append(f"\n💰 Total spend: ${plan.get('total_cost', 0):.0f} / ${plan.get('budget', 0):.0f}")
        text = "\n".join(lines)

        resp = _get_slack().chat_postMessage(channel=channel, text=text)
        return json.dumps({"ok": True, "ts": resp["ts"]})
    except SlackApiError as exc:
        return json.dumps({"ok": False, "error": str(exc.response["error"])})
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def post_approval_request(approval_json: str) -> str:
    """
    Post a Slack notification asking the supply-chain manager to approve
    a held high-value order.

    Args:
        approval_json: JSON string from approval_tools.check_approval_required.

    Returns:
        JSON with 'ok' and Slack 'ts'.
    """
    channel = os.environ.get("SLACK_CHANNEL", "#supply-chain")
    try:
        data    = json.loads(approval_json)
        flagged = data.get("flagged_drugs", [])
        ids     = data.get("approval_ids", [])

        lines = [
            "⚠️ *Approval Required — High-Value Pharma Order*\n",
            f"The following drug categories require manager sign-off: *{', '.join(flagged)}*",
            f"Approval IDs: `{ids}`",
            "\nPlease approve or reject via the dashboard or `/api/approve/<id>`.",
        ]
        text = "\n".join(lines)
        resp = _get_slack().chat_postMessage(channel=channel, text=text)
        return json.dumps({"ok": True, "ts": resp["ts"]})
    except SlackApiError as exc:
        return json.dumps({"ok": False, "error": str(exc.response["error"])})
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})
