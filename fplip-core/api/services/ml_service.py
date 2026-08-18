"""
ML Service for FPLIP API.
Handles scrap risk prediction using the trained model.
"""

import json
import joblib
from pathlib import Path
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
if not MODEL_DIR.exists():
    MODEL_DIR = Path("ml/models")
MODEL_PATH = MODEL_DIR / "scrap_model.joblib"
METADATA_PATH = MODEL_DIR / "scrap_metadata.json"

class ScrapRiskModel:
    """Singleton wrapper for the scrap risk model."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Load the model and metadata from disk."""
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run training script first.")

        self.pipeline = joblib.load(MODEL_PATH)

        with open(METADATA_PATH, 'r') as f:
            self.metadata = json.load(f)

        self.feature_names = self.metadata['feature_names']
        self.risk_threshold = self.metadata['risk_threshold']

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict scrap risk for a given set of features.

        Args:
            features: Dict of feature names to values.
                     Must include all feature_names from training.

        Returns:
            Dict with probability, risk_band, and top_factors.
        """
        # Build feature vector in correct order
        feature_vector = [features.get(name, 0) for name in self.feature_names]

        # Get probability
        prob = float(self.pipeline.predict_proba([feature_vector])[0][1])

        # Determine risk band
        if prob >= self.risk_threshold + 0.2:
            risk_band = "high"
        elif prob >= self.risk_threshold:
            risk_band = "elevated"
        else:
            risk_band = "normal"

        # Compute top factors
        # Get the coefficient contributions
        classifier = self.pipeline.named_steps['classifier']
        scaler = self.pipeline.named_steps['scaler']

        # Standardize the feature vector
        feature_scaled = scaler.transform([feature_vector])[0]
        coefficients = classifier.coef_[0]

        # Compute contributions (coefficient * standardized feature value)
        contributions = []
        for name, coef, val_scaled in zip(self.feature_names, coefficients, feature_scaled):
            contrib = coef * val_scaled
            contributions.append((name, contrib))

        # Sort by absolute contribution and take top 3
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        top_factors = [
            {
                "feature": name,
                "impact": float(contrib),
                "direction": "increases" if contrib > 0 else "decreases"
            }
            for name, contrib in contributions[:3]
        ]

        return {
            "probability": prob,
            "risk_band": risk_band,
            "risk_threshold": self.risk_threshold,
            "top_factors": top_factors,
        }

# Singleton instance
_scrap_model = None

def get_scrap_model() -> ScrapRiskModel:
    """Get the singleton scrap risk model."""
    global _scrap_model
    if _scrap_model is None:
        _scrap_model = ScrapRiskModel()
    return _scrap_model
