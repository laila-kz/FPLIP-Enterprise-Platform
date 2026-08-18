#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/run_pipeline_ci.sh <execution_date>
# This version runs directly with `airflow dags test` (no Docker)

EXECUTION_DATE="${1:-$(date +%Y-%m-%d)}"

echo "=========================================="
echo "FPLIP Pipeline Run (CI/Headless)"
echo "Execution Date: $EXECUTION_DATE"
echo "=========================================="

# Ensure Airflow home and dbt profile are set
export AIRFLOW_HOME="${AIRFLOW_HOME:-$GITHUB_WORKSPACE}"
export AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW_HOME}/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-$HOME/.dbt}"

# Verify dbt is available
if ! command -v dbt &> /dev/null; then
  echo "dbt not found in PATH. Make sure dbt is installed in the same environment."
  exit 1
fi

echo "dbt found at: $(which dbt)"

# Verify DAGs folder exists
if [ ! -d "$AIRFLOW_HOME/dags" ]; then
  echo "DAGs folder not found at $AIRFLOW_HOME/dags"
  echo "Creating DAGs folder..."
  mkdir -p "$AIRFLOW_HOME/dags"
fi

# Step 1: Run ingestion_dag
 echo ""
 echo "=== [1/4] Running ingestion_dag ==="
 airflow dags test ingestion_dag "$EXECUTION_DATE"

# Step 2: Install dbt package dependencies
 echo ""
 echo "=== [2/4] Installing dbt package dependencies ==="
 cd "${GITHUB_WORKSPACE:-$PWD}/dbt"
 dbt deps --profiles-dir "${DBT_PROFILES_DIR:-$HOME/.dbt}"

# Step 3: Run dbt_transform_dag
 echo ""
 echo "=== [3/4] Running dbt_transform_dag ==="
 airflow dags test dbt_transform_dag "$EXECUTION_DATE"

# Step 4: Run data_quality_dag
 echo ""
 echo "=== [4/4] Running data_quality_dag ==="
 airflow dags test data_quality_dag "$EXECUTION_DATE"

# Complete
 echo ""
 echo "=========================================="
 echo "Pipeline completed successfully for $EXECUTION_DATE"
 echo "=========================================="