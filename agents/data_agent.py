"""
agents/data_agent.py
====================
ADK agent that validates an uploaded sales CSV and engineers features
for downstream agents.
"""
from google.adk.agents import Agent
from tools.data_tools import validate_and_engineer

data_agent = Agent(
    name="data_agent",
    model="gemini-2.0-flash",
    description=(
        "Validates pharmaceutical sales CSV files and engineers time-series "
        "features for each ATC drug category."
    ),
    instruction=(
        "You are a data validation and feature engineering specialist. "
        "When given a file path, call validate_and_engineer to check that "
        "the file contains the required columns and return a JSON summary "
        "of the latest row's engineered features. "
        "If validation fails, report the specific error clearly. "
        "Do not modify the file — only read and analyse it."
    ),
    tools=[validate_and_engineer],
)
