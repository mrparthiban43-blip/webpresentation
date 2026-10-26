"""Synthetic usage telemetry mirroring Databricks system tables and Snowflake ACCOUNT_USAGE.

Column names follow `system.billing.usage` and `WAREHOUSE_METERING_HISTORY`, so real
connectors can replace this generator without changing downstream models. Planted
anomalies are returned as ground truth for evaluating detection and the agent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DBU_PRICE_USD = {"JOBS_COMPUTE": 0.15, "ALL_PURPOSE_COMPUTE": 0.55, "SQL_COMPUTE": 0.22}
SNOWFLAKE_CREDIT_USD = 3.0

JOBS = [
    ("job_ingest_orders", "data-eng", "JOBS_COMPUTE", 40.0),
    ("job_ingest_payments", "data-eng", "JOBS_COMPUTE", 28.0),
    ("job_silver_customers", "data-eng", "JOBS_COMPUTE", 35.0),
    ("job_ml_features", "ml-platform", "JOBS_COMPUTE", 60.0),
    ("nb_adhoc_analyst", "analytics", "ALL_PURPOSE_COMPUTE", 25.0),
    ("sql_dashboards", "analytics", "SQL_COMPUTE", 45.0),
]

WAREHOUSES = [
    ("WH_TRANSFORM", "data-eng", 2.0),
    ("WH_BI", "analytics", 1.0),
    ("WH_ADHOC", "analytics", 0.5),
    ("WH_ML", "ml-platform", 1.5),
]

ANOMALY_COLUMNS = [
    "anomaly_id",
    "platform",
    "entity",
    "type",
    "start_date",
    "end_date",
    "expected_extra_usd",
    "description",
]


@dataclass(frozen=True)
class GeneratedTelemetry:
    databricks_usage: pd.DataFrame
    snowflake_metering: pd.DataFrame
    anomalies: pd.DataFrame


def generate(days: int = 90, seed: int = 42, end_date: str = "2026-10-20") -> GeneratedTelemetry:
    if days < 30:
        raise ValueError("days must be at least 30 so anomalies fit inside the window")

    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=end_date, periods=days, freq="D")

    dbx = _databricks_usage(rng, dates)
    sf = _snowflake_metering(rng, dates)
    anomalies = _plant_anomalies(dbx, sf, dates)
    return GeneratedTelemetry(dbx, sf, anomalies)


def _databricks_usage(rng: np.random.Generator, dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    for job_id, team, sku, base_dbus in JOBS:
        weekday_factor = np.where(dates.dayofweek < 5, 1.0, 0.35)
        noise = rng.normal(1.0, 0.08, len(dates)).clip(0.6, None)
        dbus = base_dbus * weekday_factor * noise
        rows.append(
            pd.DataFrame(
                {
                    "usage_date": dates,
                    "workspace_id": "ws-prod-001",
                    "sku_name": sku,
                    "job_id": job_id,
                    "owner_team": team,
                    "usage_quantity": dbus.round(2),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    df["usd_cost"] = (df["usage_quantity"] * df["sku_name"].map(DBU_PRICE_USD)).round(2)
    return df


def _snowflake_metering(rng: np.random.Generator, dates: pd.DatetimeIndex) -> pd.DataFrame:
    hours = pd.date_range(dates[0], dates[-1] + pd.Timedelta(hours=23), freq="h")
    rows = []
    for name, team, size_credits in WAREHOUSES:
        business = ((hours.hour >= 8) & (hours.hour < 20) & (hours.dayofweek < 5)).astype(float)
        load = np.where(name == "WH_TRANSFORM", 1.0 - 0.5 * business, business * 0.8 + 0.05)
        noise = rng.normal(1.0, 0.15, len(hours)).clip(0.3, None)
        credits = (size_credits * load * noise).clip(0, size_credits)
        rows.append(
            pd.DataFrame(
                {
                    "start_time": hours,
                    "warehouse_name": name,
                    "owner_team": team,
                    "credits_used_compute": credits.round(4),
                    "credits_used_cloud_services": (credits * 0.03).round(4),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    df["usd_cost"] = (
        (df["credits_used_compute"] + df["credits_used_cloud_services"]) * SNOWFLAKE_CREDIT_USD
    ).round(2)
    return df


def _plant_anomalies(
    dbx: pd.DataFrame, sf: pd.DataFrame, dates: pd.DatetimeIndex
) -> pd.DataFrame:
    """Mutate the frames in place with three realistic cost incidents."""
    records = []

    # 1. Runaway job: a code change makes the ML features job 4x more expensive.
    start, end = dates[-12], dates[-6]
    mask = (dbx["job_id"] == "job_ml_features") & dbx["usage_date"].between(start, end)
    price = dbx.loc[mask, "sku_name"].map(DBU_PRICE_USD)
    extra = (dbx.loc[mask, "usage_quantity"] * 3 * price).sum()
    dbx.loc[mask, "usage_quantity"] *= 4
    dbx.loc[mask, "usd_cost"] *= 4
    records.append(
        _record(1, "databricks", "job_ml_features", "runaway_job", start, end, extra,
                "Job DBU consumption jumped 4x after a code change.")
    )

    # 2. Idle warehouse: auto-suspend disabled, WH_ADHOC burns credits all night.
    start, end = dates[-25], dates[-15]
    mask = (sf["warehouse_name"] == "WH_ADHOC") & sf["start_time"].between(
        start, end + pd.Timedelta(hours=23)
    )
    extra = ((0.5 - sf.loc[mask, "credits_used_compute"]) * SNOWFLAKE_CREDIT_USD).sum()
    sf.loc[mask, "credits_used_compute"] = 0.5
    sf.loc[mask, "usd_cost"] = round(0.5 * 1.03 * SNOWFLAKE_CREDIT_USD, 2)
    records.append(
        _record(2, "snowflake", "WH_ADHOC", "idle_warehouse", start, end, extra,
                "Warehouse ran at full load 24x7 because auto-suspend was disabled.")
    )

    # 3. Interactive compute used for scheduled work.
    start, end = dates[-20], dates[-1]
    mask = (dbx["job_id"] == "nb_adhoc_analyst") & dbx["usage_date"].between(start, end)
    extra = (dbx.loc[mask, "usage_quantity"] * (0.55 - 0.15)).sum()
    records.append(
        _record(3, "databricks", "nb_adhoc_analyst", "wrong_compute_type", start, end, extra,
                "Scheduled workload runs on all-purpose compute; jobs compute is ~73% cheaper.")
    )

    return pd.DataFrame(records, columns=ANOMALY_COLUMNS)


def _record(idx, platform, entity, kind, start, end, extra, description) -> dict:
    return {
        "anomaly_id": f"A{idx:03d}",
        "platform": platform,
        "entity": entity,
        "type": kind,
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "expected_extra_usd": round(float(extra), 2),
        "description": description,
    }
