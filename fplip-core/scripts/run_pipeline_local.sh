#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/run_pipeline.sh <execution_date>
# Example: ./scripts/run_pipeline.sh 2026-08-03

EXECUTION_DATE="${1:-$(date +%Y-%m-%d)}"

echo "=========================================="
echo "FPLIP Pipeline Run"
echo "Execution Date: $EXECUTION_DATE"
echo "=========================================="

# ============================================
# Step 1: Run ingestion_dag
# ============================================
echo ""
echo "=== [1/3] Running ingestion_dag ==="
docker compose exec -T airflow-scheduler airflow dags test ingestion_dag "$EXECUTION_DATE"

# ============================================
# Step 2: Run dbt_transform_dag
# ============================================
echo ""
echo "=== [2/3] Running dbt_transform_dag ==="
docker compose exec -T airflow-scheduler airflow dags test dbt_transform_dag "$EXECUTION_DATE"

# ============================================
# Step 3: Run data_quality_dag
# ============================================
echo ""
echo "=== [3/3] Running data_quality_dag ==="
docker compose exec -T airflow-scheduler airflow dags test data_quality_dag "$EXECUTION_DATE"

# ============================================
# Complete
# ============================================
echo ""
echo "=========================================="
echo "✅ Pipeline completed successfully for $EXECUTION_DATE"
echo "=========================================="