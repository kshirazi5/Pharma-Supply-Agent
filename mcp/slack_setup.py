"""
mcp/slack_setup.py
==================
MCP Slack server configuration.
This script documents how to wire up the @modelcontextprotocol/server-slack
Node.js MCP server so ADK agents can post to Slack via the MCP toolset.

To start the MCP server:
    npx -y @modelcontextprotocol/server-slack

Required env vars (set in .env):
    SLACK_BOT_TOKEN  — xoxb- bot token
    SLACK_TEAM_ID    — workspace team ID
"""
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()


def start_slack_mcp_server():
    """Start the Node.js Slack MCP server as a subprocess."""
    env = {
        **os.environ,
        "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN", ""),
        "SLACK_TEAM_ID"  : os.environ.get("SLACK_TEAM_ID", ""),
    }
    print("Starting @modelcontextprotocol/server-slack ...")
    proc = subprocess.Popen(
        ["npx", "-y", "@modelcontextprotocol/server-slack"],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return proc


if __name__ == "__main__":
    proc = start_slack_mcp_server()
    proc.wait()
