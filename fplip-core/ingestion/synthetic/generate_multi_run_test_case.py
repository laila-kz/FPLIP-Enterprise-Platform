"""
Generate a deliberate multi-run test case for fact grain validation.
This creates a CSV file that can be loaded into Bronze via the existing
ingestion pipeline.
"""

import csv
import datetime
from pathlib import Path


def generate_multi_run_test_case():
    """Generate a test case with two runs on same machine/shift/product/day"""

    # Ensure data/incoming directory exists
    incoming_dir = Path("data/incoming")
    incoming_dir.mkdir(parents=True, exist_ok=True)

    # Fixed test date
    test_date = datetime.date(2026, 7, 25)

    records = [
        {
            "machine_id": "M01",
            "shift_id": "S1",
            "product_id": "P-BLOCK-01",
            "run_date": test_date.isoformat(),
            "run_sequence_number": 1,
            "run_start_time": "2026-07-25 08:00:00",
            "run_end_time": "2026-07-25 10:30:00",
            "planned_units": 1000,
            "produced_units": 980,
            "good_units": 960,
        },
        {
            "machine_id": "M01",
            "shift_id": "S1",
            "product_id": "P-BLOCK-01",
            "run_date": test_date.isoformat(),
            "run_sequence_number": 2,
            "run_start_time": "2026-07-25 13:00:00",
            "run_end_time": "2026-07-25 15:45:00",
            "planned_units": 1200,
            "produced_units": 1150,
            "good_units": 1120,
        },
    ]

    # Write to CSV - this will be picked up by the ingestion pipeline
    output_file = incoming_dir / "production_runs_multi_run_test.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Generated multi-run test case: {output_file}")
    print(f"   - Machine: M01, Shift: S1, Product: P-BLOCK-01, Date: {test_date}")
    print("   - Run 1: sequence 1, 8:00-10:30, 980 units")
    print("   - Run 2: sequence 2, 13:00-15:45, 1150 units")
    return str(output_file)


def generate_second_multi_run_test_case():
    """Generate a second multi-run case on a different machine for validation."""
    incoming_dir = Path("data/incoming")
    incoming_dir.mkdir(parents=True, exist_ok=True)

    test_date = datetime.date(2026, 7, 26)
    records = [
        {
            "machine_id": "M02",
            "shift_id": "S1",
            "product_id": "P-PAVE-02",
            "run_date": test_date.isoformat(),
            "run_sequence_number": 1,
            "run_start_time": "2026-07-26 06:00:00",
            "run_end_time": "2026-07-26 08:30:00",
            "planned_units": 400,
            "produced_units": 380,
            "good_units": 350,
        },
        {
            "machine_id": "M02",
            "shift_id": "S1",
            "product_id": "P-PAVE-02",
            "run_date": test_date.isoformat(),
            "run_sequence_number": 2,
            "run_start_time": "2026-07-26 09:30:00",
            "run_end_time": "2026-07-26 12:00:00",
            "planned_units": 450,
            "produced_units": 430,
            "good_units": 410,
        },
        {
            "machine_id": "M02",
            "shift_id": "S1",
            "product_id": "P-PAVE-02",
            "run_date": test_date.isoformat(),
            "run_sequence_number": 3,
            "run_start_time": "2026-07-26 13:00:00",
            "run_end_time": "2026-07-26 15:30:00",
            "planned_units": 500,
            "produced_units": 480,
            "good_units": 460,
        },
    ]

    output_file = incoming_dir / "production_multi_run_3_20260726.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Generated second multi-run test case: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    generate_multi_run_test_case()
    generate_second_multi_run_test_case()
