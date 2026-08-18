"""
ingestion_dag.py — Bronze Layer Ingestion

Tasks:
- extract_production, extract_downtime, extract_qc (parallel)
- validate_contracts
- load_bronze_bigquery

Dependencies:
[extract_production, extract_downtime, extract_qc] >> validate_contracts >> load_bronze_bigquery
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from pathlib import Path
import os


def resolve_repo_root() -> str:
    if os.environ.get("GITHUB_WORKSPACE"):
        return str(Path(os.environ["GITHUB_WORKSPACE"]).resolve())

    path = Path(__file__).resolve()
    for parent in [path, *path.parents]:
        if (parent / "ingestion").exists():
            return str(parent)
    if path.parent.name == "dags":
        return str(path.parent.parent)
    return str(path.parent)

REPO_ROOT = resolve_repo_root()

# Default arguments for all tasks
default_args = {
    "owner": "fplip",
    # CI-friendly: avoid long-running retry loops. Use 0 retries so failures
    # surface immediately; change to 1 with a short delay if you prefer one retry.
    "retries": 0,
    "retry_delay": timedelta(seconds=10),
    "retry_exponential_backoff": False,
    "max_retry_delay": timedelta(minutes=1),
    # Per-task execution timeout (safety net) - prevents tasks from hanging
    # indefinitely in CI. Individual tasks also specify this.
    "execution_timeout": timedelta(minutes=15),
}

with DAG(
    dag_id="ingestion_dag",
    default_args=default_args,
    params={"repo_root": REPO_ROOT},
    schedule=None,  # Triggered externally (by run_pipeline.sh)
    catchup=False,
    max_active_runs=1,
    start_date=datetime(2024, 1, 1),
    tags=["fplip", "bronze"],
) as dag:

    # ============================================================
    # Task 1: Extract Production
    # ============================================================
    extract_production = BashOperator(
        task_id="extract_production",
        bash_command=(
            "export PYTHONPATH={{ params.repo_root }}:$PYTHONPATH && cd {{ params.repo_root }} && "
            "python -c \"from ingestion.extract_and_load import extract_and_load_production; "
            "from datetime import datetime; "
            "extract_and_load_production(datetime.strptime('{{ ds }}', '%Y-%m-%d').date())\""
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ============================================================
    # Task 2: Extract Downtime
    # ============================================================
    extract_downtime = BashOperator(
        task_id="extract_downtime",
        bash_command=(
            "export PYTHONPATH={{ params.repo_root }}:$PYTHONPATH && cd {{ params.repo_root }} && "
            "python -c \"from ingestion.extract_and_load import extract_and_load_downtime; "
            "from datetime import datetime; "
            "extract_and_load_downtime(datetime.strptime('{{ ds }}', '%Y-%m-%d').date())\""
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ============================================================
    # Task 3: Extract QC
    # ============================================================
    extract_qc = BashOperator(
        task_id="extract_qc",
        bash_command=(
            "export PYTHONPATH={{ params.repo_root }}:$PYTHONPATH && cd {{ params.repo_root }} && "
            "python -c \"from ingestion.extract_and_load import extract_and_load_qc; "
            "from datetime import datetime; "
            "extract_and_load_qc(datetime.strptime('{{ ds }}', '%Y-%m-%d').date())\""
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ============================================================
    # Task 4: Validate Contracts (Not a separate script — validation is inside extract_and_load)
    # ============================================================
    # Note: Validation is already inside extract_and_load, so we skip this step.
    # The validation happens as part of each extract task.
    # We'll keep this as a placeholder or remove it.

    # ============================================================
    # Task 5: Load Bronze BigQuery
    # ============================================================
    # Note: Loading is already inside extract_and_load, so we skip this step too.
    # The load happens as part of each extract task.

    # ============================================================
    # Dependencies
    # ============================================================
    # All three extract tasks run in parallel; validation and load are handled inside each extract task.
    # No explicit downstream dependencies are required.
