import json
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import pandas as pd


class AnomalyDetector:
    """Anomaly detection inference class using Isolation Forest + rules hybrid."""
    
    def __init__(self, model_dir: str = "ml/models/saved"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = None
        self._load_model()

    def _load_model(self):
        """Load serialized model artifacts."""
        try:
            self.model = joblib.load(self.model_dir / "anomaly_model_iso.pkl")
            self.scaler = joblib.load(self.model_dir / "anomaly_model_scaler.pkl")
            self.feature_names = joblib.load(self.model_dir / "anomaly_model_features.pkl")
            with open(self.model_dir / "anomaly_model_metadata.json", "r") as f:
                self.metadata = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load anomaly model artifacts: {e}")

    def _rule_scan(self, row: Dict) -> Dict:
        """Apply rule-based anomaly filters."""
        score = 0.0
        reasons: List[str] = []

        # Rule 1: Zero or extreme amounts
        amount = float(row.get("billed_amount", 0))
        if amount == 0 or amount > 50000:
            score += 1.0
            reasons.append("extreme_amount")

        # Rule 2: Recent repeat claim
        if int(row.get("is_recent_repeat_claim", 0)) == 1:
            score += 1.0
            reasons.append("recent_repeat")

        # Rule 3: High-risk combination (mismatch + frequent claimer)
        if (int(row.get("is_code_mismatch", 0)) == 1 and 
            int(row.get("is_frequent_claimer", 0)) == 1):
            score += 1.0
            reasons.append("high_risk_combo")

        return {
            "rule_score": score,
            "rule_reasons": reasons if reasons else ["normal"]
        }

    def predict(self, input_data: Dict) -> Dict:
        """Predict anomaly for single record using hybrid model."""
        # Ensure feature order matches training
        row = {k: input_data.get(k, 0) for k in self.feature_names}
        X = pd.DataFrame([row], columns=self.feature_names)
        X_scaled = self.scaler.transform(X)

        # Isolation Forest: -1 = anomaly, 1 = normal
        iso_pred = int(self.model.predict(X_scaled)[0])
        iso_score = float(self.model.score_samples(X_scaled)[0])
        iso_flag = 1 if iso_pred == -1 else 0

        # Rule-based layer
        rule_out = self._rule_scan(input_data)
        
        # Hybrid flag: OR logic (catch more anomalies)
        final_flag = 1 if (iso_flag == 1 or rule_out["rule_score"] > 0) else 0

        return {
            "isolation_prediction": iso_pred,
            "isolation_flag": iso_flag,
            "anomaly_score": round(iso_score, 6),
            "rule_score": rule_out["rule_score"],
            "rule_reasons": rule_out["rule_reasons"],
            "is_flagged": bool(final_flag),
            "risk_level": "HIGH" if final_flag else "LOW"
        }

    def get_model_info(self) -> Dict:
        """Return model metadata."""
        return {
            "model_type": self.metadata.get("model_type", "Unknown"),
            "training_date": self.metadata.get("training_date", "Unknown"),
            "dataset_size": self.metadata.get("dataset_size", 0),
            "features": self.metadata.get("features", []),
            "contamination": self.metadata.get("contamination", None),
            "metrics": self.metadata.get("metrics", {}),
            "rules": self.metadata.get("rules", [])
        }


_detector_instance: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    """Singleton getter for anomaly detector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AnomalyDetector()
    return _detector_instance