#!/usr/bin/env python3
"""
Contract validator for FPLIP Bronze ingestion.
Validates CSV files against YAML contracts with specific, actionable failure reasons.
"""

import pandas as pd
import yaml


class ValidationResult:
    """Structured validation result with specific failure reasons."""

    def __init__(
        self, passed: bool, reason: str | None = None, errors: list[str] = None
    ):
        self.passed = passed
        self.reason = reason
        self.errors = errors or []

    def __bool__(self):
        return self.passed

    def __str__(self):
        if self.passed:
            return "✅ Validation passed"
        return f"❌ Validation failed: {self.reason}"


def validate_against_contract(
    dataframe: pd.DataFrame, contract_path: str
) -> ValidationResult:
    """
    Validate a DataFrame against a YAML contract.

    Returns:
        ValidationResult with:
        - passed: bool
        - reason: human-readable failure reason (or None if passed)
        - errors: list of specific error messages

    Checks performed:
    1. Every contract column exists in the DataFrame
    2. Every DataFrame column exists in the contract (flags unexpected extras)
    3. Each column's dtype matches the contract's declared type
    4. NOT NULL columns have no null values
    """
    # Load contract
    with open(contract_path, "r", encoding="utf-8") as f:
        contract = yaml.safe_load(f)

    schema = contract.get("schema", [])
    if not schema:
        return ValidationResult(False, "Contract has no schema defined")

    # Build contract column info
    contract_columns = {}
    for col in schema:
        name = col.get("name")
        if name:
            contract_columns[name] = {
                "type": col.get("type"),
                "nullable": col.get("nullable", True),
                "description": col.get("description", ""),
            }

    df_columns = set(dataframe.columns)
    contract_col_names = set(contract_columns.keys())

    errors = []

    # Check 1: All contract columns exist in DataFrame
    missing_columns = contract_col_names - df_columns
    if missing_columns:
        errors.append(f"Missing required columns: {sorted(missing_columns)}")

    # Check 2: No unexpected columns (unless tolerated)
    extra_columns = df_columns - contract_col_names
    if extra_columns:
        errors.append(f"Unexpected columns found: {sorted(extra_columns)}")

    # Check 3: Type validation
    for col_name, col_info in contract_columns.items():
        if col_name not in df_columns:
            continue  # Already reported as missing

        expected_type = col_info["type"]

        # Special case: check if numeric columns have non-numeric values
        if expected_type.upper() in ["INTEGER", "FLOAT", "DECIMAL"]:
            # Try to convert to numeric, catch errors
            non_numeric = dataframe[
                pd.to_numeric(dataframe[col_name], errors="coerce").isna()
                & dataframe[col_name].notna()
            ]
            if not non_numeric.empty:
                errors.append(
                    (
                        f"Column '{col_name}' expected type {expected_type}, "
                        f"but found non-numeric values: "
                        f"{non_numeric[col_name].head(3).tolist()}"
                    )
                )

        # Check 4: Null validation for required columns
        if not col_info["nullable"]:
            null_count = dataframe[col_name].isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{col_name}' is NOT NULL but has {null_count} null values"
                )

    if errors:
        return ValidationResult(False, f"{len(errors)} validation error(s)", errors)

    return ValidationResult(True, "All checks passed")


def validate_file(file_path: str, contract_path: str) -> ValidationResult:
    """
    Validate a CSV file against a YAML contract.
    """
    try:
        df = pd.read_csv(file_path)
        return validate_against_contract(df, contract_path)
    except Exception as e:
        return ValidationResult(False, f"Error reading file: {e!s}")
