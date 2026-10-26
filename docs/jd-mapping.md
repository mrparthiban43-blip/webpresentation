# Forward Deployed Engineer requirements mapped to this project

Telephony and voice are out of scope. The text channel (chat and API) stands in for voice, and
the same engineering applies: agent design, integrations, observability, evals and client delivery.

| Requirement | How the project proves it | Phase |
|---|---|---|
| Design, prompt, build and deploy production agents with guardrails and tool calling | Cost-investigation agent with versioned prompts, read-only tools, PII masking | 5 |
| REST APIs, WebSockets, webhooks, callbacks, CRM writes | FastAPI service, streaming over WebSocket, inbound webhooks, ticket and Slack writes | 6 |
| LangChain, OpenAI SDKs | LangGraph workflow on the OpenAI SDK | 5 |
| Logs, traces, root-cause analysis (prompt vs platform vs data) | Per-step tracing and an RCA playbook, backed by a real data pipeline | 7 |
| Agent metrics and funnel experiments | Golden set scored on completion, hallucination, latency, cost; prompt A/B report | 8 |
| Python or Java backend, OAuth2 and JWT | Python and FastAPI with JWT and role-based access | 6 |
| Cloud, preferably GCP | Cloud Run and Secret Manager deployment | 9 |
| Data fluency (SQL, Python) | Databricks and Snowflake pipeline, SQL run analytics | 2, 3, 7 |
| Client technical leadership and plain-language communication | Workshop deck, integration guide, demo script | 9 |
| RAG | Runbook retrieval with citations | 5 |

## Interview story
"I delivered an AI agent end to end: the data platform underneath it, the integrations around it,
the tracing that lets me prove why it fails, and the evals that show it improving."
