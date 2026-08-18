from datetime import date

from ingestion.extract_and_load import extract_and_load


class DummyValidationResult:
    def __init__(self):
        self.passed = True
        self.reason = ""
        self.errors = []


def test_extract_and_load_falls_back_to_synthetic_production_file(
    tmp_path, monkeypatch
):
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir()

    fallback_file = incoming_dir / "production_runs_multi_run_test.csv"
    fallback_file.write_text(
        "machine_id,shift_id,product_id,run_date\nM01,1,P001,2026-07-25\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "ingestion.extract_and_load.validate_file",
        lambda *args, **kwargs: DummyValidationResult(),
    )
    monkeypatch.setattr(
        "ingestion.extract_and_load.load_file_to_bronze", lambda *args, **kwargs: 1
    )

    rows_loaded = extract_and_load(
        "production",
        date(2026, 7, 25),
        incoming_dir=str(incoming_dir),
    )

    assert rows_loaded == 1
