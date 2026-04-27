import json
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd


class DenialPredictor:
    def __init__(self, model_dir: str = "ml/models/saved"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = None
        self.threshold = 0.5
        self._load_model()

    def _load_model(self):
        try:
            self.model = joblib.load(self.model_dir / "denial_model.pkl")
            self.scaler = joblib.load(self.model_dir / "denial_model_scaler.pkl")
            self.feature_names = joblib.load(self.model_dir / "denial_model_features.pkl")
            with open(self.model_dir / "denial_model_metadata.json", "r") as f:
                self.metadata = json.load(f)
            self.threshold = float(self.metadata.get("chosen_threshold", 0.5))
        except Exception as exc:
            raise RuntimeError(f"Failed to load denial model artifacts: {exc}") from exc

    def prepare_features(self, input_data: Dict) -> pd.DataFrame:
        df = pd.DataFrame([input_data])
        categorical_features = [
            "insurance_type",
            "procedure_cpt_code",
            "diagnosis_code",
            "place_of_service",
            "claim_type",
            "network_status",
        ]
        df_encoded = pd.get_dummies(df, columns=categorical_features, drop_first=True)

        for feature in self.feature_names:
            if feature not in df_encoded.columns:
                df_encoded[feature] = 0

        return df_encoded[self.feature_names]

    def predict(self, input_data: Dict) -> Dict:
        X = self.prepare_features(input_data)
        X_scaled = self.scaler.transform(X)
        probability = float(self.model.predict_proba(X_scaled)[0][1])
        prediction = int(probability >= self.threshold)

        if probability >= 0.7:
            risk_level = "HIGH"
        elif probability >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "denial_probability": round(probability, 4),
            "risk_level": risk_level,
            "prediction": prediction,
            "prediction_label": "Denied" if prediction == 1 else "Approved",
            "top_risk_factors": self._get_top_risk_factors(X, n=3),
        }

    def predict_batch(self, input_data_list: List[Dict]) -> List[Dict]:
        predictions = []
        for input_data in input_data_list:
            try:
                predictions.append(self.predict(input_data))
            except Exception as exc:
                predictions.append(
                    {
                        "error": str(exc),
                        "denial_probability": None,
                        "risk_level": "ERROR",
                    }
                )
        return predictions

    def _get_top_risk_factors(self, X: pd.DataFrame, n: int = 3) -> List[Dict]:
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importances = np.abs(self.model.coef_[0])
        else:
            return []

        feature_data = []
        for i, (feature, importance) in enumerate(zip(self.feature_names, importances)):
            feature_data.append(
                {
                    "feature": feature,
                    "value": float(X.iloc[0, i]),
                    "importance": float(importance),
                }
            )

        feature_data.sort(key=lambda item: item["importance"], reverse=True)
        return feature_data[:n]

    def get_model_info(self) -> Dict:
        return {
            "model_type": self.metadata.get("model_type", "Unknown"),
            "training_date": self.metadata.get("training_date", "Unknown"),
            "training_data_size": self.metadata.get("dataset_size", 0),
            "num_features": self.metadata.get("num_features", 0),
            "metrics": self.metadata.get("metrics", {}),
            "top_features": self.metadata.get("top_features", []),
            "chosen_threshold": self.threshold,
        }

    def get_feature_importance(self) -> List[Dict]:
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            importances = np.abs(self.model.coef_[0])
        else:
            return []

        feature_importance = [
            {"feature": feature, "importance": float(importance)}
            for feature, importance in zip(self.feature_names, importances)
        ]
        feature_importance.sort(key=lambda item: item["importance"], reverse=True)
        return feature_importance


_predictor_instance: Optional[DenialPredictor] = None


def get_predictor() -> DenialPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = DenialPredictor()
    return _predictor_instance
