"""
agents/risk_agent.py
====================
Core decision agent: recalls adaptive memory, scores cross-category risk,
detects anomalies, optimises orders under budget, and gates high-value orders.
"""
from google.adk.agents import Agent
from tools.risk_tools      import score_risk, optimise_orders
from tools.memory_tools    import recall_past_decisions, log_decision
from tools.anomaly_tools   import detect_anomaly, detect_all_anomalies
from tools.approval_tools  import check_approval_required

risk_agent = Agent(
    name="risk_agent",
    model="gemini-2.5-flash",
    description=(
        "The core procurement decision agent. Combines forecasts with historical "
        "memory, anomaly detection, and budget optimisation to produce a final "
        "order plan and gate high-value purchases for human approval."
    ),
    instruction=(
        "You are the senior supply-chain risk analyst for a pharmaceutical distributor. "
        "Your job is to produce a safe, budget-optimised procurement order each day.\n\n"
        "Step-by-step process:\n"
        "1. For each drug in the forecast, call recall_past_decisions to check recent history. "
        "   If false_surge_rate > 0.3, reduce your confidence for that drug.\n"
        "2. Call detect_all_anomalies with the CSV file path to identify abnormal spikes. "
        "   Anomalous drugs should receive a 20% volume buffer.\n"
        "3. Call score_risk on the forecast JSON to get cross-category risk scores.\n"
        "4. Call optimise_orders with the forecast JSON and the available budget.\n"
        "5. Call check_approval_required on the order plan to gate high-value orders.\n"
        "6. For every drug, call log_decision to record the decision with full reasoning.\n"
        "7. Return a concise final summary: which drugs are ordered, quantities, costs, "
        "   which (if any) are pending approval, and your risk reasoning."
    ),
    tools=[
        score_risk,
        optimise_orders,
        recall_past_decisions,
        log_decision,
        detect_anomaly,
        detect_all_anomalies,
        check_approval_required,
    ],
)
