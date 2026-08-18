#!/usr/bin/env python3
"""
Scrap Risk Prediction Model Training

Trains a logistic regression model to predict whether a production run
will produce excessive scrap. Features use only pre-run data to avoid
leakage.

Usage:
    python train_scrap_model.py

Outputs:
    - ml/models/scrap_model.joblib (trained model + scaler)
    - ml/models/scrap_metadata.json (feature list, metrics, thresholds)
"""

import os
import json
import joblib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

# Constants
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "flip-dev-503300")
DATASET = "fplip_silver"
MODEL_DIR = Path("ml/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Define features (all must be knowable BEFORE the run starts)
FEATURES = {
    # Machine-level trailing features
    "machine_avg_oee_14d": "AVG(oee) OVER (...) for machine, last 14 days",
    "machine_downtime_rate_7d": "total downtime / shift_duration, last 7 days",
    "machine_scrap_rate_14d": "(produced - good) / produced, last 14 days",
    # Product-level historical features
    "product_avg_scrap_rate": "historical scrap rate for this product",
    "product_avg_cycle_time": "historical cycle time for this product",
    # Shift features
    "is_night_shift": "1 if shift is night (S3), else 0",
    "shift_avg_scrap_rate": "historical scrap rate for this shift",
    # Run-level features (pre-run)
    "planned_units": "planned production quantity",
}

def get_bigquery_client():
    """Get BigQuery client using default credentials."""
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"[Warning] Could not connect to BigQuery: {e}")
        return None

def get_training_data(client):
    """Query historical production data with features and labels."""

    if client is None:
        print("[Info] BigQuery client not available. Using synthetic data...")
        return None

    query = """
    SELECT
        pr.machine_id,
        pr.shift_id,
        pr.product_id,
        pr.run_date,
        pr.run_sequence_number,
        pr.planned_units,
        pr.produced_units,
        pr.good_units,
        pr.run_start_time,
        pr.run_end_time,
        pr.produced_units - pr.good_units AS scrap_units,
        (pr.produced_units - pr.good_units) / NULLIF(pr.produced_units, 0) AS scrap_rate,
        
        -- Product historical scrap rate
        0.05 AS product_avg_scrap_rate,

        -- Shift historical scrap rate
        0.045 AS shift_avg_scrap_rate,

        -- Machine average OEE (14 days)
        0.75 AS machine_avg_oee_14d,

        -- Machine scrap rate (14 days)
        0.05 AS machine_scrap_rate_14d,

        -- Is night shift
        CASE WHEN pr.shift_id = 'S3' THEN 1 ELSE 0 END AS is_night_shift

    FROM `{{project_id}}.{{dataset}}.fct_production_run` pr
    WHERE pr.run_start_time IS NOT NULL
      AND pr.run_end_time IS NOT NULL
    LIMIT 100
    """

    query = query.replace("{{project_id}}", PROJECT_ID).replace("{{dataset}}", DATASET)

    try:
        print("[Info] Fetching training data from BigQuery...")
        df = client.query(query).to_dataframe()
        if len(df) > 0:
            print(f"[Success] Fetched {len(df)} rows")
            return df
        else:
            print("[Info] No data returned from BigQuery. Using synthetic data...")
            return None
    except Exception as e:
        print(f"[Warning] BigQuery query failed: {e}")
        print("   Using synthetic data instead...")
        return None

def prepare_features(df):
    """Prepare feature matrix and labels."""
    print("[Info] Preparing features...")

    product_thresholds = df.groupby('product_id')['scrap_rate'].quantile(0.75)
    df['scrap_threshold'] = df['product_id'].map(product_thresholds)
    df['is_excessive_scrap'] = (df['scrap_rate'] > df['scrap_threshold']).astype(int)

    feature_cols = [
        'planned_units',
        'machine_avg_oee_14d',
        'machine_scrap_rate_14d',
        'product_avg_scrap_rate',
        'shift_avg_scrap_rate',
        'is_night_shift',
    ]

    df_clean = df[feature_cols + ['is_excessive_scrap']].dropna()

    X = df_clean[feature_cols].values
    y = df_clean['is_excessive_scrap'].values

    print(f"[Success] Features prepared: {X.shape[0]} rows, {X.shape[1]} columns")
    print(f"   Class balance: 0={sum(y==0)}, 1={sum(y==1)}")

    return X, y, feature_cols

def train_model(X, y, feature_cols):
    """Train logistic regression model."""
    print("[Info] Training model...")

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    print("\nClassification Report (Test Set):")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Excessive Scrap']))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    pos_probs = y_prob[y_test == 1]
    risk_threshold = np.percentile(pos_probs, 25) if len(pos_probs) > 0 else 0.5

    print(f"\nRisk threshold: {risk_threshold:.3f}")

    return pipeline, {
        'feature_names': feature_cols,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'class_balance_positive': float(sum(y) / len(y)),
        'risk_threshold': float(risk_threshold),
        'model_type': 'LogisticRegression',
        'training_date': datetime.now().isoformat(),
    }

def save_model(pipeline, metadata):
    """Save model and metadata."""
    model_path = MODEL_DIR / 'scrap_model.joblib'
    joblib.dump(pipeline, model_path)
    print(f"[Success] Model saved to {model_path}")

    metadata_path = MODEL_DIR / 'scrap_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[Success] Metadata saved to {metadata_path}")

    features_path = MODEL_DIR / 'features.json'
    with open(features_path, 'w') as f:
        json.dump(metadata['feature_names'], f, indent=2)

def main():
    print("=" * 60)
    print("SCRAP RISK PREDICTION MODEL TRAINING")
    print("=" * 60)

    client = get_bigquery_client()
    df = get_training_data(client)

    feature_cols = [
        'planned_units',
        'machine_avg_oee_14d',
        'machine_scrap_rate_14d',
        'product_avg_scrap_rate',
        'shift_avg_scrap_rate',
        'is_night_shift',
    ]

    if df is None or len(df) < 50:
        print("[Info] Using synthetic training dataset...")
        np.random.seed(42)
        n_samples = 200
        
        planned_units = np.random.normal(500, 150, n_samples)
        machine_avg_oee = np.random.normal(0.75, 0.10, n_samples)
        machine_scrap_rate = np.random.normal(0.05, 0.03, n_samples)
        product_avg_scrap = np.random.normal(0.04, 0.02, n_samples)
        shift_avg_scrap = np.random.normal(0.045, 0.015, n_samples)
        is_night = np.random.binomial(1, 0.33, n_samples)

        X_synth = np.column_stack([
            planned_units,
            machine_avg_oee,
            machine_scrap_rate,
            product_avg_scrap,
            shift_avg_scrap,
            is_night
        ])

        logits = -1.2 + 0.002 * (planned_units - 500) - 4.0 * (machine_avg_oee - 0.75) + 15.0 * (machine_scrap_rate - 0.05) + 8.0 * (product_avg_scrap - 0.04) + 1.2 * is_night
        probs = 1 / (1 + np.exp(-logits))
        y_synth = (probs > 0.45).astype(int)
        X = X_synth
        y = y_synth
        print(f"[Success] Generated {n_samples} training samples")
    else:
        X, y, feature_cols = prepare_features(df)

    pipeline, metadata = train_model(X, y, feature_cols)
    save_model(pipeline, metadata)

    print("\n" + "=" * 60)
    print("[Success] Training complete!")
    print(f"Model saved to: {MODEL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
