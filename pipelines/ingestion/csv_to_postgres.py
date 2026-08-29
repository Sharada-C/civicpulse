"""
Stage-1 ingestion path (README §5): CSV -> Python -> validation -> PostgreSQL.
Later replaced/complemented by the Kafka streaming path (kafka/producers, kafka/consumers)
once Module 9 real-time ingestion is built.
"""
import argparse
import os
import sys

import pandas as pd
from sqlalchemy import create_engine

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from validation.validate_complaints import validate_dataframe  # noqa: E402

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://civicpulse:changeme@localhost:5433/civicpulse"
)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def ingest(csv_path: str, table: str = "staging_complaints"):
    df = load_csv(csv_path)
    print(f"Read {len(df)} rows from {csv_path}")

    valid_df, report = validate_dataframe(df)
    print(
        f"Valid: {report['valid']} | Duplicates: {report['duplicates']} | "
        f"Invalid: {report['invalid']} | Missing required fields: {report['missing']}"
    )

    engine = create_engine(DATABASE_URL)
    valid_df.to_sql(table, engine, if_exists="append", index=False)
    print(f"Loaded {len(valid_df)} valid rows into '{table}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--table", default="staging_complaints")
    args = parser.parse_args()
    ingest(args.csv_path, args.table)
