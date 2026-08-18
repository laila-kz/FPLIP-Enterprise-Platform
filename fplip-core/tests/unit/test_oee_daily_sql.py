from pathlib import Path


def test_oee_daily_uses_weighted_run_performance_rollup():
    sql_path = Path(__file__).resolve().parents[2] / "dbt" / "models" / "gold" / "oee_daily.sql"
    sql_text = sql_path.read_text(encoding="utf-8")

    assert "calculated_performance" in sql_text
    assert "sum(calculated_performance * run_duration_sec)" in sql_text
