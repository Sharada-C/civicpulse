import os

import pandas as pd
from sqlalchemy import create_engine, text


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://civicpulse:changeme@localhost:5433/civicpulse",
)


SEVERITY_SCORE = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    "CRITICAL": 1.00,
}


def build_date_key(dt: pd.Timestamp) -> int:
    return int(dt.strftime("%Y%m%d"))


def load_dim_date(conn, complaints_df):
    dates = pd.to_datetime(
        complaints_df["created_at"]
    ).dt.normalize().unique()

    for date in dates:
        dt = pd.Timestamp(date)

        conn.execute(
            text("""
                INSERT INTO dim_date (
                    date_key,
                    full_date,
                    day,
                    month,
                    year,
                    quarter,
                    day_of_week,
                    is_weekend
                )
                VALUES (
                    :date_key,
                    :full_date,
                    :day,
                    :month,
                    :year,
                    :quarter,
                    :day_of_week,
                    :is_weekend
                )
                ON CONFLICT (date_key) DO NOTHING
            """),
            {
                "date_key": build_date_key(dt),
                "full_date": dt.date(),
                "day": dt.day,
                "month": dt.month,
                "year": dt.year,
                "quarter": dt.quarter,
                "day_of_week": dt.dayofweek,
                "is_weekend": dt.dayofweek >= 5,
            },
        )


def load_dim_location(conn):
    conn.execute(
        text("""
            INSERT INTO dim_location (
                location_id,
                ward_code,
                ward_name,
                latitude,
                longitude,
                population
            )
            SELECT
                l.location_id,
                w.ward_code,
                w.name,
                l.latitude,
                l.longitude,
                w.population
            FROM locations l
            JOIN wards w
                ON l.ward_id = w.ward_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM dim_location dl
                WHERE dl.location_id = l.location_id
            )
        """)
    )


def load_dim_category(conn):
    conn.execute(
        text("""
            INSERT INTO dim_category (
                category_id,
                category_name
            )
            SELECT
                c.category_id,
                c.name
            FROM categories c
            WHERE NOT EXISTS (
                SELECT 1
                FROM dim_category dc
                WHERE dc.category_id = c.category_id
            )
        """)
    )


def load_dim_department(conn):
    conn.execute(
        text("""
            INSERT INTO dim_department (
                department_id,
                department_name
            )
            SELECT
                d.department_id,
                d.name
            FROM departments d
            WHERE NOT EXISTS (
                SELECT 1
                FROM dim_department dd
                WHERE dd.department_id = d.department_id
            )
        """)
    )


def load_fact_complaints(conn):
    result = conn.execute(
        text("""
            INSERT INTO fact_complaints (
                complaint_id,
                date_key,
                location_key,
                category_key,
                department_key,
                severity_score,
                resolution_time_days,
                status,
                is_repeat_complaint
            )
            SELECT
                c.complaint_id,

                CAST(
                    TO_CHAR(c.created_at, 'YYYYMMDD')
                    AS INTEGER
                ) AS date_key,

                dl.location_key,

                dc.category_key,

                dd.department_key,

                CASE c.severity
                    WHEN 'LOW' THEN 0.25
                    WHEN 'MEDIUM' THEN 0.50
                    WHEN 'HIGH' THEN 0.75
                    WHEN 'CRITICAL' THEN 1.00
                END AS severity_score,

                CASE
                    WHEN c.resolved_at IS NOT NULL
                    THEN EXTRACT(
                        EPOCH FROM (
                            c.resolved_at - c.created_at
                        )
                    ) / 86400.0
                    ELSE NULL
                END AS resolution_time_days,

                c.status,

                EXISTS (
                    SELECT 1
                    FROM complaints previous
                    WHERE previous.complaint_id <> c.complaint_id
                      AND previous.category_id = c.category_id
                      AND previous.location_id = c.location_id
                      AND previous.created_at < c.created_at
                      AND previous.created_at >=
                          c.created_at - INTERVAL '30 days'
                ) AS is_repeat_complaint

            FROM complaints c

            JOIN dim_location dl
                ON dl.location_id = c.location_id

            JOIN dim_category dc
                ON dc.category_id = c.category_id

            LEFT JOIN dim_department dd
                ON dd.department_id = c.department_id

            WHERE NOT EXISTS (
                SELECT 1
                FROM fact_complaints fc
                WHERE fc.complaint_id = c.complaint_id
            )
        """)
    )

    return result.rowcount


def update_fact_predictions(conn):
    predictions_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            "processed",
            "complaint_predictions.csv",
        )
    )

    if not os.path.exists(predictions_path):
        print(
            "Prediction file not found. "
            "Skipping prediction update."
        )
        return 0

    predictions = pd.read_csv(
        predictions_path
    )

    required_columns = {
        "complaint_id",
        "predicted_severity",
        "predicted_resolution_days",
    }

    missing_columns = (
        required_columns
        - set(predictions.columns)
    )

    if missing_columns:
        raise ValueError(
            "Prediction file is missing columns: "
            f"{sorted(missing_columns)}"
        )

    predictions = predictions[
        [
            "complaint_id",
            "predicted_severity",
            "predicted_resolution_days",
        ]
    ].drop_duplicates(
        subset=["complaint_id"]
    )

    conn.execute(
        text("""
            CREATE TEMP TABLE temp_complaint_predictions (
                complaint_id INTEGER,
                predicted_severity VARCHAR(20),
                predicted_resolution_days NUMERIC(6,2)
            ) ON COMMIT DROP
        """)
    )

    predictions.to_sql(
        "temp_complaint_predictions",
        conn,
        if_exists="append",
        index=False,
    )

    result = conn.execute(
        text("""
            UPDATE fact_complaints fc
            SET
                predicted_severity =
                    p.predicted_severity,
                predicted_resolution_days =
                    p.predicted_resolution_days
            FROM temp_complaint_predictions p
            WHERE fc.complaint_id = p.complaint_id
        """)
    )

    return result.rowcount


def run():
    engine = create_engine(
        DATABASE_URL
    )

    with engine.begin() as conn:

        print("Loading dim_date...")

        complaints_df = pd.read_sql(
            text("""
                SELECT created_at
                FROM complaints
            """),
            conn,
        )

        if complaints_df.empty:
            print(
                "No complaints found. Nothing to load."
            )
            return

        load_dim_date(
            conn,
            complaints_df,
        )

        print(
            "dim_date loaded."
        )

        print(
            "Loading dim_location..."
        )

        load_dim_location(
            conn
        )

        print(
            "dim_location loaded."
        )

        print(
            "Loading dim_category..."
        )

        load_dim_category(
            conn
        )

        print(
            "dim_category loaded."
        )

        print(
            "Loading dim_department..."
        )

        load_dim_department(
            conn
        )

        print(
            "dim_department loaded."
        )

        print(
            "Loading fact_complaints..."
        )

        fact_count = load_fact_complaints(
            conn
        )

        print(
            f"fact_complaints loaded: "
            f"{fact_count} rows."
        )

        print(
            "Updating ML predictions..."
        )

        prediction_count = (
            update_fact_predictions(
                conn
            )
        )

        print(
            f"ML predictions updated: "
            f"{prediction_count} rows."
        )


if __name__ == "__main__":
    run()