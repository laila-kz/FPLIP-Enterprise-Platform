"""
Master data ingestion DAG for FPLIP Week 3.
Loads master data (machines, products, shifts, downtime reasons, defect types)
using full-table overwrite pattern.
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


def load_all_master_data():
    """Load all five master datasets into Bronze."""
    from ingestion.master_data_loader import load_master_file

    base_path = Path("data/incoming")
    master_files = {
        "machines": "machines.csv",
        "products": "products.csv",
        "shifts": "shifts.csv",
        "downtime_reasons": "downtime_reasons.csv",
        "defect_types": "defect_types.csv",
    }

    results = {}
    for table_name, file_name in master_files.items():
        file_path = base_path / file_name
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        rows = load_master_file(str(file_path), table_name)
        results[table_name] = rows

    print(f"✅ Loaded all master data: {results}")
    return results


with DAG(
    dag_id="load_master_data",
    start_date=datetime(2026, 7, 1),
    schedule="@weekly",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "fplip",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
) as dag:
    load_task = PythonOperator(
        task_id="load_all_master_data",
        python_callable=load_all_master_data,
    )
