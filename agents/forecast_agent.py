"""
agents/forecast_agent.py
========================
ADK agent that runs demand forecasting models for all 8 drug categories.
"""
from google.adk.agents import Agent
from tools.forecast_tools import run_forecast

forecast_agent = Agent(
    name="forecast_agent",
    model="gemini-2.0-flash",
    description=(
        "Runs XGBoost + Random Forest volume forecasts and Logistic Regression "
        "surge classification for all 8 ATC pharmaceutical drug categories."
    ),
    instruction=(
        "You are a pharmaceutical demand forecasting specialist. "
        "When given a JSON features payload (from data_agent), call run_forecast "
        "to obtain ensemble volume predictions and surge probability for each drug. "
        "Clearly summarise which drugs are flagged as surge risk (surge_prob >= 0.5). "
        "Return the full forecast JSON for downstream use by the risk agent."
    ),
    tools=[run_forecast],
)
