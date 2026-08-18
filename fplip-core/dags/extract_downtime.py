"""
Downtime ingestion DAG for FPLIP Week 2.
Extracts downtime CSV, validates against contract, loads to Bronze.
"""

from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator


def _run_downtime(**context):
    from ingestion.extract_and_load import extract_and_load_downtime

    target_date = context["logical_date"].date()
    extract_and_load_downtime(target_date)


with DAG(
    dag_id="extract_downtime",
    start_date=datetime.now(timezone.utc) - timedelta(days=1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "fplip",
        "retries": 3,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
    },
) as dag:
    run_task = PythonOperator(
        task_id="extract_validate_load_downtime",
        python_callable=_run_downtime,
    )
