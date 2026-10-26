# ADR 001: Hosted LLM with tool calling, no model training

**Status:** Accepted

**Context:** The assistant must answer cost questions accurately and cheaply. Training or
fine-tuning a model needs labelled data we do not have and adds cost without improving factual
accuracy on structured data.

**Decision:** Use a hosted LLM with tool calling over a governed MCP layer. Detection is
deterministic. A small ML model (forecasting) may be added later only if evals show lift.

**Consequences:** Accuracy comes from tools and data quality, not model weights. We must
evaluate answers against ground truth and track latency and token cost per request.
