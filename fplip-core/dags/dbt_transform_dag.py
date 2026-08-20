"""
dbt_transform_dag.py — Silver and Gold Transformations

Tasks:
- dbt_run_silver
- dbt_run_gold_oee
- dbt_run_gold_scrap

Dependencies:
dbt_run_silver >> [dbt_run_gold_oee, dbt_run_gold_scrap]
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# ============================================================
# FIX: Use the correct dbt path (found via docker exec)
# ============================================================
# The dbt executable is at /opt/airflow/.venv-fplip/bin/dbt inside the container
DBT_CMD = "/opt/airflow/.venv-fplip/bin/dbt"

# ============================================================
# Default arguments for all tasks
# ============================================================
default_args = {
    "owner": "fplip",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=15),
}

with DAG(
    dag_id="dbt_transform_dag",
    default_args=default_args,
    schedule=None,  # Triggered externally
    catchup=False,
    max_active_runs=1,
    start_date=datetime(2024, 1, 1),
    tags=["fplip", "dbt", "transform"],
) as dag:

    # ============================================================
    # Task 1: dbt Run Silver
    # ============================================================
    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=(
            f"cd /opt/airflow/dbt && "
            f"{DBT_CMD} run --select silver"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ============================================================
    # Task 2: dbt Run Gold OEE
    # ============================================================
    dbt_run_gold_oee = BashOperator(
        task_id="dbt_run_gold_oee",
        bash_command=(
            f"cd /opt/airflow/dbt && "
            f"{DBT_CMD} run --select oee_daily"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Task 3: dbt Run Gold Scrap
    # ============================================================
    dbt_run_gold_scrap = BashOperator(
        task_id="dbt_run_gold_scrap",
        bash_command=(
            f"cd /opt/airflow/dbt && "
            f"{DBT_CMD} run --select scrap_root_cause_summary"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Dependencies
    # ============================================================
    dbt_run_silver >> [dbt_run_gold_oee, dbt_run_gold_scrap]