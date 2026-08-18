"""
data_quality_dag.py — Data Quality Validation

Tasks:
- dbt_test_silver
- dbt_test_gold
- notify_success

Dependencies:
dbt_test_silver >> dbt_test_gold >> notify_success
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pathlib import Path
import os
import json
import urllib.request
import shutil


def resolve_repo_root() -> Path:
    if os.environ.get("GITHUB_WORKSPACE"):
        return Path(os.environ["GITHUB_WORKSPACE"]).resolve()

    path = Path(__file__).resolve()
    for parent in [path, *path.parents]:
        if (parent / "dbt").exists():
            return parent
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
    "retries": 0 if CI_MODE else 2,
    "retry_delay": timedelta(seconds=5) if CI_MODE else timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(seconds=10) if CI_MODE else timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=10),
}


def post_slack_message(text: str) -> None:
    """Post a message to Slack via webhook."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
        print("✅ Slack notification sent")
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {e}")


def notify_success(**context):
    """Send a success notification to Slack."""
    ds = context.get("ds", "unknown date")
    message = (
        f"✅ FPLIP pipeline completed successfully\n"
        f"Date: {ds}\n"
        f"All Silver and Gold models refreshed and passed quality checks."
    )
    post_slack_message(message)


def notify_failure(context):
    """Send a failure notification to Slack (callback)."""
    task_id = context.get("task_instance", {}).task_id
    dag_id = context.get("dag", {}).dag_id
    ds = context.get("ds", "unknown date")
    exception = context.get("exception", "Unknown error")

    message = (
        f"❌ FPLIP pipeline failure\n"
        f"DAG: `{dag_id}`\n"
        f"Task: `{task_id}`\n"
        f"Date: {ds}\n"
        f"Error: {exception}"
    )
    post_slack_message(message)


with DAG(
    dag_id="data_quality_dag",
    default_args=default_args,
    schedule=None,  # Triggered externally
    catchup=False,
    max_active_runs=1,
    start_date=datetime(2024, 1, 1),
    tags=["fplip", "dbt", "quality"],
    on_failure_callback=notify_failure,
) as dag:

    # ============================================================
    # Task 1: dbt Test Silver
    # ============================================================
    dbt_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=(
            f"cd {REPO_ROOT}/dbt && "
            f"{DBT_CMD} deps --profiles-dir \"{DBT_PROFILES_DIR}\" && "
            f"{DBT_CMD} test --profiles-dir \"{DBT_PROFILES_DIR}\" --select +silver"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Task 2: dbt Test Gold
    # ============================================================
    dbt_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=(
            f"cd {REPO_ROOT}/dbt && "
            f"{DBT_CMD} deps --profiles-dir \"{DBT_PROFILES_DIR}\" && "
            f"{DBT_CMD} test --profiles-dir \"{DBT_PROFILES_DIR}\" --select +gold"
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ============================================================
    # Task 3: Notify Success
    # ============================================================
    notify_success_task = PythonOperator(
        task_id="notify_success",
        python_callable=notify_success,
        provide_context=True,
    )

    # ============================================================
    # Dependencies
    # ============================================================
    dbt_test_silver >> dbt_test_gold >> notify_success_task