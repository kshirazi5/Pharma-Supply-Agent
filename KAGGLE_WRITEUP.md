# KAGGLE WRITEUP DRAFT
(Paste into the Kaggle Writeup editor. ~1,400 words — well under the 2,500 limit.)

---

**Title:** Pharma Supply Intelligence: A 5-Agent Procurement System That Prevents Drug Shortages

**Subtitle:** Multi-agent demand forecasting, anomaly detection, and budget-optimised ordering with human-in-the-loop approvals — built on Google ADK, Gemini, and MCP

**Track:** Agents for Business

**Created by:** Kamran Shirazi & Minahil Saba

---

## The Problem

Pharmaceutical distributors walk a tightrope every single day. Order too little of a drug and pharmacies run out — patients with asthma, chronic pain, or anxiety disorders can't fill prescriptions. Order too much and capital is locked up in inventory that expires on the shelf. Wasted medicine is wasted money, and in pharma the stakes of getting it wrong are measured in both dollars and patient health.

Today this balancing act is mostly manual. A procurement analyst eyeballs last week's sales, applies gut feel, and places orders. This process breaks down in three ways:

1. **Demand surges are invisible until it's too late.** Flu season, heat waves, and local outbreaks create sudden spikes in specific drug categories that simple averages miss.
2. **Anomalies get treated as trends.** A one-off bulk purchase by a single clinic looks like a demand surge and triggers over-ordering.
3. **No institutional memory.** When an analyst over-orders because of a false surge signal, nothing stops the same mistake next month.

## The Solution

**Pharma Supply Intelligence** is a five-agent system that turns a daily sales CSV into a safe, budget-optimised procurement order — with a human manager kept in the loop for high-value decisions.

A procurement analyst uploads the day's sales data to a Next.js dashboard. From there, a Google ADK multi-agent pipeline takes over:

- **Data Agent** (gemini-2.0-flash) validates the CSV and engineers time-series features (lags, rolling means, seasonality) for 8 ATC drug categories.
- **Forecast Agent** (gemini-2.0-flash) runs per-category XGBoost + Random Forest ensemble models to forecast demand volume, plus a logistic-regression classifier that outputs a surge probability.
- **Risk Agent** (gemini-2.5-flash) is the decision core. It recalls past ordering decisions from Supabase, runs IsolationForest anomaly detection to separate genuine surges from statistical flukes, scores cross-category risk, and optimises the order plan under a hard budget constraint. Any order above the approval threshold is gated for human sign-off.
- **Alert Agent** (gemini-2.0-flash) posts decision summaries and approval requests to Slack via an MCP server, so managers see decisions where they already work.
- **Orchestrator** (gemini-2.5-flash) coordinates the whole pipeline sequentially, enforces workflow rules (stop on validation failure, escalate on low confidence), and routes data between agents.

## Why Agents?

This problem is genuinely agentic — a single prompt or a static ML script can't solve it:

- **The workflow is conditional.** Whether an order executes, escalates, or pauses depends on forecast confidence, anomaly flags, historical false-surge rates, and budget headroom. Agents reason over these signals; a pipeline of if-statements can't explain *why* it decided.
- **It requires memory across runs.** The Risk Agent queries its own past decisions ("this drug triggered 3 false surge alerts in the last 10 runs — lower confidence") before ordering. That adaptive feedback loop is the difference between a forecaster and a *learning* procurement system.
- **Humans must stay in control.** Autonomous ordering of $40,000 in pharmaceuticals is a non-starter. The system pauses (a long-running operation) when cost exceeds a threshold, persists the pending order, and resumes only when a manager approves or rejects it from the dashboard.

## Architecture

*(Attach the architecture diagram image here — same diagram as in the repo README)*

```
CSV Upload (Next.js + JWT auth)
        │
        ▼
FastAPI Backend ──► Orchestrator Agent (gemini-2.5-flash)
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   Data Agent ──► Forecast Agent ──► Risk Agent ──► Alert Agent
   (validate,      (XGBoost/RF        (memory,        (Slack via
    features)       ensemble +         anomalies,      MCP server)
                    surge LR)          budget opt,
                                       approval gate)
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                        Supabase                Human approval
                  (decisions, outcomes,        (manager dashboard,
                   pending_approvals)           approve/reject)
```

**Tech stack:** Google ADK (agents), Gemini 2.0/2.5 Flash (reasoning), XGBoost / scikit-learn (forecasting + anomaly models), MCP Slack server (notifications), Supabase (long-term memory + approval state), FastAPI (backend, JWT auth), Next.js (dashboard), Docker (deployment).

## Course Concepts Demonstrated

1. **Multi-agent system (ADK)** — a root orchestrator with four specialised sub-agents in a sequential pipeline (`agents/orchestrator.py`). Each sub-agent is an LLM-powered ADK `Agent` with its own toolset.
2. **MCP Server** — the Alert Agent posts to Slack through the `@modelcontextprotocol/server-slack` MCP server (`mcp/slack_setup.py`).
3. **Custom tools** — seven tool modules (`tools/`) covering data validation, ML inference, risk scoring, anomaly detection, memory recall/logging, approval gating, and alerting.
4. **Long-running operations** — high-value orders pause as `pending_approvals` rows in Supabase and resume when a manager acts, surviving process restarts.
5. **Sessions & long-term memory** — every decision is logged with reasoning; the Risk Agent recalls the last N decisions per drug and computes a false-surge rate that tempers future confidence.
6. **Security features** — JWT-based auth with role separation (analyst vs. manager), all secrets in environment variables (never in source), CORS restrictions, and human approval gates on high-value actions.
7. **Deployability** — fully containerised with Docker; runs on any container host (Cloud Run-ready).

## The Build Journey

The project evolved through three versions. V1 was a single agent that called one forecasting tool — it worked, but its reasoning was a black box and it happily "ordered" $200k of inventory against a $50k budget. V2 split forecasting from decision-making, which immediately made failures debuggable: bad orders traced to bad forecasts or bad risk logic, never both. V3 added the pieces that make it production-shaped: adaptive memory (the false-surge feedback loop), IsolationForest anomaly detection to stop one-off bulk purchases from masquerading as demand surges, the human approval gate, and the Slack MCP integration.

The hardest design decision was where to put the intelligence. Early versions let the LLM compute order quantities — impressive in demos, unreliable in practice. The final architecture uses deterministic ML models and optimisation code for the *numbers*, and Gemini agents for the *judgment*: interpreting signals, applying workflow rules, writing human-readable reasoning for every logged decision. LLMs decide *what matters*; code decides *how much*.

Trained on a real Kaggle pharma sales dataset (2014–2019, 8 ATC categories), the ensemble forecaster achieves solid accuracy on held-out data, and the anomaly detector correctly flags injected synthetic spikes while letting seasonal surges through.

## Value

For a mid-sized distributor, even a 10% reduction in emergency orders and expired stock is worth six figures annually. But the deeper value is trust: every order the system places carries logged reasoning, an audit trail in Supabase, and a human sign-off above a configurable threshold. It's an agent system a compliance-conscious pharma business could actually adopt.

## Links

- **Code (public GitHub):** https://github.com/kshirazi5/Pharma-Supply-Agent
- **Video:** [YouTube URL — attach in Media Gallery]

---
---

# VIDEO SCRIPT (≤5 minutes)

**Format:** screen recording + voiceover. Rough timing below.

**[0:00–0:40] Problem** — Slide with a pharmacy shelf image.
"Pharmaceutical distributors face a daily gamble: under-order and patients can't fill prescriptions; over-order and capital dies as expired stock. Today this is done manually — an analyst, a spreadsheet, and gut feel. Demand surges get missed, one-off anomalies trigger over-ordering, and the same mistakes repeat because nothing remembers."

**[0:40–1:20] Why agents** — Slide with the 5 agents.
"This needs more than a forecast model. The workflow is conditional — decisions depend on confidence, anomalies, history, and budget. It needs memory across runs. And it needs a human in the loop before real money moves. That's an agent problem. I built a five-agent system on Google's Agent Development Kit, powered by Gemini."

**[1:20–2:10] Architecture** — Show the README Mermaid diagram.
"A Data Agent validates and engineers features. A Forecast Agent runs XGBoost ensembles per drug category. The Risk Agent — the brain — recalls past decisions from Supabase, runs anomaly detection, and optimises orders under budget. The Alert Agent posts to Slack through an MCP server. An Orchestrator coordinates everything sequentially. Security is built in: JWT auth, role separation, secrets in env vars, and an approval gate — any order over the threshold pauses until a manager signs off. That's a long-running operation that survives restarts."

**[2:10–4:10] Demo** — Live screen recording:
1. Log into the dashboard, upload `salesdaily.csv`.
2. Show the pipeline result: per-drug orders, risk scores, surge/anomaly flags.
3. Point out one drug marked PENDING APPROVAL — "this order exceeded $10,000, so the system stopped itself."
4. Show the Slack message arriving with the approval request.
5. Switch to the manager role, open the Approvals panel, approve the order.
6. Show the decisions table — "every decision is logged with the agent's reasoning. Next run, the Risk Agent reads this history and lowers its confidence for drugs with false surge alerts."

**[4:10–4:50] The build + deployability** — Show the repo, then `docker build`.
"Built with ADK in Python, Gemini 2.0 and 2.5 Flash, FastAPI, Next.js, and Supabase. The whole backend ships as a single Docker container — deployable to Cloud Run in one command. The code, setup instructions, and architecture docs are on GitHub."

**[4:50–5:00] Close.**
"Pharma Supply Intelligence: agents that forecast, reason, remember — and know when to ask a human. Thanks for watching."

---
---

# SUBMISSION CHECKLIST (deadline: TONIGHT July 6, 11:59 PM PT)

1. ☐ Commit + push these changes to GitHub (auth fix, README diagram, concepts table)
2. ☐ Make the repo **public**: GitHub → Settings → Danger Zone → Change visibility
3. ☐ Record the ≤5-min video (script above) and upload to **YouTube** (public or unlisted)
4. ☐ Take a dashboard screenshot or export the architecture diagram as the **cover image**
5. ☐ On the competition page: **Join Hackathon** → **New Writeup**
6. ☐ Paste Title, Subtitle, body (above); select track **Agents for Business**
7. ☐ Media Gallery: attach cover image + YouTube video (both REQUIRED)
8. ☐ Attach project link: the public GitHub repo URL
9. ☐ Click **Save**, then **Submit** (top-right) — a saved draft does NOT count
