# Architecture

## Goals
1. Answer "why did our data platform cost change?" with evidence and dollar impact.
2. Be safe by construction: the agent can only call read-only, allow-listed tools.
3. Be measurable: detection and agent answers are scored against known incidents.

## Data flow
| Layer | Tech | Contents |
|---|---|---|
| Landing | Azure ADLS Gen2 | Raw exports of `system.billing.usage`, Snowflake `WAREHOUSE_METERING_HISTORY` |
| Bronze | Databricks, Delta | Append-only raw, with ingestion metadata |
| Silver | Databricks, PySpark | Typed, deduplicated, one cost grain across both platforms |
| Gold | Snowflake, dbt | `fct_daily_cost`, `dim_entity`, `fct_anomalies`, `fct_savings_opportunities` |
| Tools | MCP server | `get_cost_summary`, `top_cost_drivers`, `list_anomalies`, `explain_anomaly`, `estimate_savings` |
| Agent | FastAPI | LLM tool-calling loop, audit log, per-request cost and latency |
| UI | React | Chat, evidence tables, cost charts |

## Detection
Deterministic first (rolling z-score on daily cost per entity, idle-time rules, SKU-fit rules).
The LLM explains and prioritises findings; it does not decide whether an anomaly exists.

## Security
- Read-only Snowflake role scoped to gold schemas; no raw SQL passthrough from the model.
- MCP tools validate arguments and cap rows.
- Secrets in Azure Key Vault in deployment, `.env` locally.

## Data source modes
- `synthetic`: generator in `src/costcopilot/generator`, schema-compatible with real tables.
- `live`: real connectors, used once Databricks and Snowflake accounts exist.
