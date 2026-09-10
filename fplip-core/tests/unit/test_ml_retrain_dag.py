"""
tests/unit/test_ml_retrain_dag.py

Tests for the ML model promotion logic in dags/utils/ml_promotion.py.

NOTE: This test file deliberately does NOT import anything from Airflow.
Airflow cannot be imported on Windows because it depends on `fcntl` (POSIX-only).
All business logic lives in ml_promotion.py, which has no Airflow dependency.
"""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# This is the ONLY module under test — no airflow imports
from dags.utils.ml_promotion import evaluate_and_promote


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_metadata(path: Path, train_size: int) -> None:
    path.write_text(json.dumps({"train_size": train_size, "features": []}))


def _make_dummy_model(path: Path) -> None:
    path.write_bytes(b"FAKE_JOBLIB_BYTES")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def model_dir(tmp_path: Path) -> Path:
    """Returns a fresh temp directory that mimics ml/models/."""
    (tmp_path / "scrap_model.joblib").write_bytes(b"FAKE")
    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFirstRunPromotion:
    """When no baseline metadata exists, the candidate should always be promoted."""

    def test_promotes_when_no_baseline(self, model_dir: Path) -> None:
        ds = "2026-04-14"
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True
        assert (model_dir / "scrap_model.joblib").exists()


class TestPromotionGate:
    """When a baseline exists, only promote if candidate ≥ baseline train_size."""

    def test_promotes_equal_train_size(self, model_dir: Path) -> None:
        ds = "2026-04-14"
        _write_metadata(model_dir / "scrap_metadata.json", train_size=100)
        _write_metadata(model_dir / "scrap_metadata_candidate.json", train_size=100)
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True

    def test_promotes_larger_train_size(self, model_dir: Path) -> None:
        ds = "2026-04-21"
        _write_metadata(model_dir / "scrap_metadata.json", train_size=80)
        _write_metadata(model_dir / "scrap_metadata_candidate.json", train_size=120)
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True

    @patch("dags.utils.ml_promotion.post_slack_message")
    def test_rejects_smaller_train_size_and_alerts(
        self, mock_slack: object, model_dir: Path
    ) -> None:
        ds = "2026-04-28"
        _write_metadata(model_dir / "scrap_metadata.json", train_size=200)
        _write_metadata(model_dir / "scrap_metadata_candidate.json", train_size=50)
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is False
        mock_slack.assert_called_once()
        alert_text = mock_slack.call_args[0][0]
        assert "50" in alert_text
        assert "200" in alert_text

    @patch("dags.utils.ml_promotion.post_slack_message")
    def test_live_model_not_overwritten_on_rejection(
        self, mock_slack: object, model_dir: Path
    ) -> None:
        ds = "2026-05-01"
        original_live_bytes = b"ORIGINAL_LIVE_MODEL"
        (model_dir / "scrap_model.joblib").write_bytes(original_live_bytes)

        _write_metadata(model_dir / "scrap_metadata.json", train_size=300)
        _write_metadata(model_dir / "scrap_metadata_candidate.json", train_size=10)
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        evaluate_and_promote(ds=ds, model_dir=model_dir)

        # Live model must still be the original bytes
        assert (model_dir / "scrap_model.joblib").read_bytes() == original_live_bytes


class TestEdgeCases:
    """Robustness against missing/corrupt files."""

    def test_promotes_when_no_candidate_metadata(self, model_dir: Path) -> None:
        ds = "2026-05-07"
        _write_metadata(model_dir / "scrap_metadata.json", train_size=100)
        # No candidate metadata file — should fall back to baseline train_size and promote
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True

    def test_promotes_on_corrupt_baseline_metadata(self, model_dir: Path) -> None:
        ds = "2026-05-14"
        (model_dir / "scrap_metadata.json").write_text("NOT_VALID_JSON{{{")
        _make_dummy_model(model_dir / f"scrap_model_{ds}.joblib")

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True  # fails safe: promote rather than block

    def test_copies_live_model_as_candidate_when_versioned_missing(
        self, model_dir: Path
    ) -> None:
        """If the versioned candidate file doesn't exist but scrap_model.joblib does,
        the function should copy it and still run the promotion gate."""
        ds = "2026-05-21"
        # No versioned candidate — live model exists (created by fixture)
        _write_metadata(model_dir / "scrap_metadata.json", train_size=50)
        _write_metadata(model_dir / "scrap_metadata_candidate.json", train_size=70)

        result = evaluate_and_promote(ds=ds, model_dir=model_dir)

        assert result is True
