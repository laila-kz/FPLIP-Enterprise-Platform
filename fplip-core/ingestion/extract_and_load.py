#!/usr/bin/env python3
"""
Extract, validate, and load pipeline for FPLIP Week 2.
Chains contract validation in front of every load.
"""

import glob
from datetime import date
from pathlib import Path

import socket
from ingestion.bronze_loader import load_file_to_bronze
from ingestion.contract_validator import validate_file

# Mapping of source name to contract path and table name
SOURCE_CONFIG = {
    "production": {
        "contract": "contracts/production.yaml",
        "table": "production_runs",
        "file_pattern": "production_{date}.csv",
        "malformed_pattern": "production_malformed_{date}.csv",
        "fallback_file": "production_runs_multi_run_test.csv",
    },
    "downtime": {
        "contract": "contracts/downtime.yaml",
        "table": "downtime_events",
        "file_pattern": "downtime_{date}.csv",
    },
    "qc": {
        "contract": "contracts/qc.yaml",
        "table": "qc_inspections",
        "file_pattern": "qc_{date}.csv",
    },
}


def extract_and_load(
    source: str,
    target_date: date,
    incoming_dir: str = "data/incoming",
    use_malformed: bool = False,
):
    """
    Extract, validate, and load a source file for a given date.

    Args:
        source: Source name ("production", "downtime", or "qc")
        target_date: Date to load
        incoming_dir: Directory containing source files
        use_malformed: If True, use malformed file for testing

    Returns:
        int: Number of rows loaded

    Raises:
        Exception: If validation fails, with the specific failure reason
    """
    config = SOURCE_CONFIG.get(source)
    if not config:
        raise ValueError(f"Unknown source: {source}")

    # Build file path
    date_str = target_date.strftime("%Y%m%d")
    if use_malformed and source == "production":
        file_pattern = config.get("malformed_pattern", config["file_pattern"])
    else:
        file_pattern = config["file_pattern"]

    file_name = file_pattern.format(date=date_str)
    candidate_names = [file_name]

    if source == "production":
        pattern = file_pattern.replace("{date}", "*")
        matching_files = sorted(glob.glob(str(Path(incoming_dir) / pattern)))
        if matching_files:
            candidate_names.extend(Path(path).name for path in matching_files)

        fallback_file = config.get("fallback_file")
        if fallback_file:
            candidate_names.append(fallback_file)

    seen_paths = set()
    file_path = None
    for candidate_name in candidate_names:
        candidate_path = Path(incoming_dir) / candidate_name
        if candidate_path in seen_paths:
            continue
        seen_paths.add(candidate_path)
        if candidate_path.exists():
            file_path = candidate_path
            break

    if file_path is None:
        searched_paths = ", ".join(
            str(Path(incoming_dir) / name) for name in candidate_names
        )
        raise FileNotFoundError(f"Source file not found. Tried: {searched_paths}")

    if file_path.name != file_name:
        print(f"⚠️ Using fallback source file: {file_path}")

    print(f"📄 Processing: {file_path}")

    # Validate against contract
    result = validate_file(str(file_path), config["contract"])

    if not result.passed:
        # Raise with the specific failure reason
        error_msg = f"Validation failed: {result.reason}"
        if result.errors:
            error_msg += f"\n  Errors: {', '.join(result.errors)}"
        raise Exception(error_msg)

    print("✅ Validation passed")

    # Load to Bronze
    # Apply a conservative global socket timeout while performing the load
    prev_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(120)
        rows_loaded = load_file_to_bronze(str(file_path), config["table"], target_date)
    finally:
        socket.setdefaulttimeout(prev_timeout)
    print(f"✅ Loaded {rows_loaded} rows into fplip_bronze.{config['table']}")

    return rows_loaded


def extract_and_load_production(target_date: date, use_malformed: bool = False):
    """Wrapper for production source."""
    return extract_and_load("production", target_date, use_malformed=use_malformed)


def extract_and_load_downtime(target_date: date):
    """Wrapper for downtime source."""
    return extract_and_load("downtime", target_date)


def extract_and_load_qc(target_date: date):
    """Wrapper for QC source."""
    return extract_and_load("qc", target_date)
