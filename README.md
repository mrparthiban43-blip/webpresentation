# LakehouseCost Copilot

An AI copilot that explains and reduces cloud data-platform spend. It ingests Databricks and
Snowflake usage telemetry, detects cost anomalies and waste, and lets an agent investigate them
through a governed MCP tool layer, surfaced in a React web app.

> **Problem:** data platform bills grow 30-50% a year and nobody can say why.
> **Solution:** a modelled cost lakehouse, deterministic detection, and an agent that cites
> evidence and quantifies savings. The LLM never writes to the platform.

## Architecture

```
Databricks system tables      Snowflake ACCOUNT_USAGE
(or synthetic generator)      (or synthetic generator)
        |                              |
        +----------- Azure ADLS Gen2 (landing) -----------+
                                |
              Databricks: Bronze -> Silver (Delta, PySpark)
                                |
              Snowflake + dbt: Gold marts (cost, anomalies)
                                |
              MCP server (read-only, allow-listed tools)
                                |
              FastAPI agent (LLM tool calling, audit log)
                                |
                        React web app
```

Details: [docs/architecture.md](docs/architecture.md). Decisions: [docs/adr](docs/adr).

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Repo standards, CI, synthetic telemetry with ground-truth anomalies | Done |
| 2 | Databricks bronze/silver pipeline | Planned |
| 3 | Snowflake gold layer with dbt and data tests | Planned |
| 4 | Anomaly detection and savings estimator | Planned |
| 5 | Agent core: tool calling, LangGraph, guardrails, RAG, MCP | Planned |
| 6 | Integrations: REST, WebSocket, webhooks, ticket writes, OAuth2/JWT | Planned |
| 7 | Observability and root-cause analysis | Planned |
| 8 | Evaluation and funnel optimisation | Planned |
| 9 | React console, GCP deployment, client kit | Planned |

How each phase maps to a Forward Deployed Engineer job description: [docs/jd-mapping.md](docs/jd-mapping.md).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\generate-telemetry      # writes data/generated/*.parquet
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\ruff check .
```

## Project tracking

Progress, skills used and the build history live in [docs/project-plan](docs/project-plan):
[PLAN.md](docs/project-plan/PLAN.md), [SKILLS.md](docs/project-plan/SKILLS.md),
[ACTIVITY_LOG.md](docs/project-plan/ACTIVITY_LOG.md). Edit `plan.json` (task status, skills),
then run `update-tracker` to regenerate them; the activity log is built from git history.

## Engineering standards

- Typed Python, `ruff` lint, `pytest`, CI on every push.
- Secrets only via environment variables; `.env` is git-ignored.
- Every pipeline layer has data-quality tests.
- Agent answers are evaluated against planted ground-truth anomalies (`evals/`).
