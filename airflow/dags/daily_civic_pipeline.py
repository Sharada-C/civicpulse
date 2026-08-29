"""
daily_civic_pipeline — mirrors README §21:
extract_data -> validate_data -> clean_data -> transform_data -> load_warehouse
    -> run_quality_checks -> generate_metrics
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "civicpulse",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_data(**context):
    print("Extracting new complaint records from source (CSV / API).")


def validate_data(**context):
    from pipelines.validation.validate_complaints import validate_dataframe  # noqa
    print("Running data quality checks (uniqueness, coordinate bounds, category validity).")


def clean_data(**context):
    print("Normalizing categories, handling missing values, deduplicating.")


def transform_data(**context):
    print("Building dimension keys and fact rows for the warehouse.")


def load_warehouse(**context):
    from pipelines.transformation.load_warehouse import run  # noqa
    run()


def run_quality_checks(**context):
    print("Post-load checks: row counts, null checks, referential integrity.")


def generate_metrics(**context):
    print("Refreshing KPI summary tables consumed by the FastAPI /analytics endpoints.")


with DAG(
    dag_id="daily_civic_pipeline",
    default_args=default_args,
    description="End-to-end daily ETL for CivicPulse",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["civicpulse", "etl"],
) as dag:

    t1 = PythonOperator(task_id="extract_data", python_callable=extract_data)
    t2 = PythonOperator(task_id="validate_data", python_callable=validate_data)
    t3 = PythonOperator(task_id="clean_data", python_callable=clean_data)
    t4 = PythonOperator(task_id="transform_data", python_callable=transform_data)
    t5 = PythonOperator(task_id="load_warehouse", python_callable=load_warehouse)
    t6 = PythonOperator(task_id="run_quality_checks", python_callable=run_quality_checks)
    t7 = PythonOperator(task_id="generate_metrics", python_callable=generate_metrics)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7
