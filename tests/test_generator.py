import pytest

from costcopilot.generator import generate


def test_generation_is_deterministic():
    a = generate(days=40, seed=7)
    b = generate(days=40, seed=7)
    assert a.databricks_usage.equals(b.databricks_usage)
    assert a.snowflake_metering.equals(b.snowflake_metering)


def test_schemas_match_platform_tables():
    t = generate(days=40)
    assert {"usage_date", "sku_name", "job_id", "usage_quantity", "usd_cost"} <= set(
        t.databricks_usage.columns
    )
    assert {"start_time", "warehouse_name", "credits_used_compute"} <= set(
        t.snowflake_metering.columns
    )


def test_no_nulls_or_negative_costs():
    t = generate(days=40)
    for df in (t.databricks_usage, t.snowflake_metering):
        assert not df.isna().any().any()
        assert (df["usd_cost"] >= 0).all()


def test_three_planted_anomalies_with_positive_impact():
    t = generate(days=40)
    assert len(t.anomalies) == 3
    assert (t.anomalies["expected_extra_usd"] > 0).all()


def test_runaway_job_is_visible_in_data():
    t = generate(days=60)
    row = t.anomalies.query("type == 'runaway_job'").iloc[0]
    job = t.databricks_usage.query("job_id == 'job_ml_features'")
    during = job[job["usage_date"].between(row.start_date, row.end_date)]["usage_quantity"].mean()
    before = job[job["usage_date"] < row.start_date]["usage_quantity"].mean()
    assert during > 2.5 * before


def test_rejects_too_short_window():
    with pytest.raises(ValueError):
        generate(days=10)
