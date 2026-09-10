"""
ml_retrain_dag.py — Automated Weekly ML Model Retraining & Evaluation

Tasks:
  - train_candidate_model: Runs train_scrap_model.py to produce versioned candidate model artifacts
  - evaluate_and_promote_model: Delegates to dags.utils.ml_promotion to evaluate & promote
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from dags.utils.ml_promotion import evaluate_and_promote


def resolve_repo_root() -> str:
    if os.environ.get("GITHUB_WORKSPACE"):
        return str(Path(os.environ["GITHUB_WORKSPACE"]).resolve())

    path = Path(__file__).resolve()
    for parent in [path, *path.parents]:
        if (parent / "ml").exists():
            return str(parent)
    if path.parent.name == "dags":
        return str(path.parent.parent)
    return str(path.parent)


REPO_ROOT = Path(resolve_repo_root())
MODEL_DIR = REPO_ROOT / "ml" / "models"


default_args = {
    "owner": "fplip",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=15),
}


def _evaluate_and_promote_task(ds: str, **context) -> bool:
    """Airflow task wrapper: calls the testable evaluate_and_promote function."""
    return evaluate_and_promote(ds=ds, model_dir=MODEL_DIR)


with DAG(
    dag_id="ml_retrain_dag",
    default_args=default_args,
    schedule="@weekly",
    catchup=False,
    max_active_runs=1,
    start_date=datetime(2024, 1, 1),
    tags=["fplip", "ml", "retrain"],
) as dag:

    train_candidate_model = BashOperator(
        task_id="train_candidate_model",
        bash_command=(
            f"export PYTHONPATH={REPO_ROOT}:$PYTHONPATH && cd {REPO_ROOT} && "
            f"python ml/training/train_scrap_model.py && "
            f"cp ml/models/scrap_model.joblib ml/models/scrap_model_{{{{ ds }}}}.joblib && "
            f"cp ml/models/scrap_metadata.json ml/models/scrap_metadata_candidate.json"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    evaluate_and_promote_model = PythonOperator(
        task_id="evaluate_and_promote_model",
        python_callable=_evaluate_and_promote_task,
        op_kwargs={"ds": "{{ ds }}"},
    )

    train_candidate_model >> evaluate_and_promote_model
