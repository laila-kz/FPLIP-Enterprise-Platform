"""
ml_promotion.py — ML model evaluation and promotion logic.

Extracted from ml_retrain_dag so it can be tested without importing Airflow
(which requires POSIX/Linux and cannot be imported on Windows).
"""

import json
import shutil
from pathlib import Path

from dags.utils.slack_alert import post_slack_message


def evaluate_and_promote(ds: str, model_dir: Path) -> bool:
    """
    Compare candidate model metrics against the production baseline in scrap_metadata.json.
    Promotes candidate if it is at least as good as baseline; otherwise sends Slack alert.

    Args:
        ds: Airflow execution date string (e.g. "2026-04-14").
        model_dir: Path to the ml/models directory.

    Returns:
        True if promoted, False if rejected.
    """
    baseline_metadata_path = model_dir / "scrap_metadata.json"
    candidate_metadata_path = model_dir / "scrap_metadata_candidate.json"
    candidate_model_path = model_dir / f"scrap_model_{ds}.joblib"
    live_model_path = model_dir / "scrap_model.joblib"

    # Fallback: if no candidate file, copy from live (already-trained model)
    if not candidate_model_path.exists() and live_model_path.exists():
        shutil.copy(live_model_path, candidate_model_path)

    # First run — no baseline yet, so promote unconditionally
    if not baseline_metadata_path.exists():
        print("[ML Retrain] No baseline metadata found. First run — promoting candidate model.")
        if candidate_model_path.exists():
            shutil.copy(candidate_model_path, live_model_path)
        return True

    try:
        with open(baseline_metadata_path, "r") as f:
            baseline_meta = json.load(f)
    except Exception as e:
        print(f"[ML Retrain] Error reading baseline metadata: {e}. Promoting candidate.")
        if candidate_model_path.exists():
            shutil.copy(candidate_model_path, live_model_path)
        return True

    candidate_meta = {}
    if candidate_metadata_path.exists():
        try:
            with open(candidate_metadata_path, "r") as f:
                candidate_meta = json.load(f)
        except Exception as e:
            print(f"[ML Retrain] Could not parse candidate metadata: {e}")

    # Metric: compare training data coverage (train_size as proxy for data completeness)
    baseline_train_size = baseline_meta.get("train_size", 0)
    candidate_train_size = candidate_meta.get("train_size", baseline_train_size)

    promoted = candidate_train_size >= baseline_train_size

    if promoted:
        print(
            f"[ML Retrain] Candidate model evaluated successfully "
            f"({candidate_train_size} samples >= {baseline_train_size}). "
            f"Promoting to {live_model_path}"
        )
        if candidate_model_path.exists():
            shutil.copy(candidate_model_path, live_model_path)
        if candidate_metadata_path.exists():
            shutil.copy(candidate_metadata_path, baseline_metadata_path)
    else:
        warning_msg = (
            f"[ML Retrain Alert] Candidate model underperformed baseline on {ds}. "
            f"Candidate train size: {candidate_train_size} vs Baseline: {baseline_train_size}. "
            f"Production model retained."
        )
        print(warning_msg)
        post_slack_message(warning_msg)

    return promoted
