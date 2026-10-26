"""CLI: write synthetic telemetry as Parquet files."""

from __future__ import annotations

import argparse
from pathlib import Path

from costcopilot.generator.telemetry import generate


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic platform usage telemetry")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/generated"))
    args = parser.parse_args(argv)

    telemetry = generate(days=args.days, seed=args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    telemetry.databricks_usage.to_parquet(args.out / "databricks_usage.parquet", index=False)
    telemetry.snowflake_metering.to_parquet(args.out / "snowflake_metering.parquet", index=False)
    telemetry.anomalies.to_csv(args.out / "ground_truth_anomalies.csv", index=False)
    print(f"Wrote telemetry for {args.days} days to {args.out}")


if __name__ == "__main__":
    main()
