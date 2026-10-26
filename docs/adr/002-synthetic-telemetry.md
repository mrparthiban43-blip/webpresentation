# ADR 002: Synthetic telemetry that mirrors real schemas

**Status:** Accepted

**Context:** Real Databricks and Snowflake accounts are not available yet, and real billing data
has no labelled incidents to evaluate against.

**Decision:** Generate telemetry with the same column names as `system.billing.usage` and
`WAREHOUSE_METERING_HISTORY`, and plant incidents with known dollar impact.

**Consequences:** Downstream code is source-agnostic, so live connectors can be swapped in.
Evals have objective ground truth. Synthetic data must never be presented as real customer data.
