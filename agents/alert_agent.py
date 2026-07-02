"""
agents/alert_agent.py
=====================
ADK agent that posts decision summaries and approval requests to Slack.
"""
from google.adk.agents import Agent
from tools.alert_tools import post_decision_summary, post_approval_request

alert_agent = Agent(
    name="alert_agent",
    model="gemini-2.0-flash",
    description=(
        "Posts pharmaceutical procurement decisions and approval requests "
        "to the configured Slack channel."
    ),
    instruction=(
        "You are a supply-chain notification agent. "
        "After the risk_agent produces a final order plan:\n"
        "• If all orders were auto-executed, call post_decision_summary with "
        "  the order plan JSON and risk JSON.\n"
        "• If any orders are pending approval, call post_approval_request "
        "  with the approval JSON.\n"
        "Always confirm whether the Slack message was successfully sent. "
        "If sending fails, report the Slack error clearly."
    ),
    tools=[post_decision_summary, post_approval_request],
)
