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
from pathlib import Path
import os
import shutil

def resolve_repo_root() -> Path:
    if os.environ.get("GITHUB_WORKSPACE"):
        return Path(os.environ["GITHUB_WORKSPACE"]).resolve()

    path = Path(__file__).resolve()
    if path.parent.name == "dags" and path.parent.parent.name == "airflow_home":
        return path.parent.parent.parent
    if path.parent.name == "dags":
        return path.parent.parent
    return path.parent

REPO_ROOT = resolve_repo_root()
DBT_CMD = shutil.which("dbt") or str(REPO_ROOT / ".venv-airflow" / "bin" / "dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", str(Path.home() / ".dbt"))
CI_MODE = os.environ.get("CI", "false").lower() in ("1", "true") or os.environ.get("GITHUB_ACTIONS") is not None

# Default arguments for all tasks
default_args = {
    "owner": "fplip",
    "retries": 0 if CI_MODE else 3,
    "retry_delay": timedelta(seconds=5) if CI_MODE else timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(seconds=10) if CI_MODE else timedelta(minutes=10),
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
    # dbt run helper
    # ============================================================

    # Task 1: dbt Run Silver
    # ============================================================
    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=(
            f"cd {REPO_ROOT}/dbt && "
            f"{DBT_CMD} deps --profiles-dir \"{DBT_PROFILES_DIR}\" && "
            f"{DBT_CMD} run --profiles-dir \"{DBT_PROFILES_DIR}\" --select +silver"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ============================================================
    # Task 2: dbt Run Gold OEE
    # ============================================================
    dbt_run_gold_oee = BashOperator(
        task_id="dbt_run_gold_oee",
        bash_command=(
            f"cd {REPO_ROOT}/dbt && "
            f"{DBT_CMD} deps --profiles-dir \"{DBT_PROFILES_DIR}\" && "
            f"{DBT_CMD} run --profiles-dir \"{DBT_PROFILES_DIR}\" --select oee_daily"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Task 3: dbt Run Gold Scrap
    # ============================================================
    dbt_run_gold_scrap = BashOperator(
        task_id="dbt_run_gold_scrap",
        bash_command=(
            f"cd {REPO_ROOT}/dbt && "
            f"{DBT_CMD} deps --profiles-dir \"{DBT_PROFILES_DIR}\" && "
            f"{DBT_CMD} run --profiles-dir \"{DBT_PROFILES_DIR}\" --select scrap_root_cause_summary"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Dependencies
    # ============================================================
    dbt_run_silver >> [dbt_run_gold_oee, dbt_run_gold_scrap]