

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]         
DATA_PATH = ROOT / "ml" / "data" / "synthetic_billing.csv"
SAVE_DIR = ROOT / "ml" / "models" / "saved"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

CATEGORICAL_FEATURES = ["insurance_type", "procedure_cpt_code", "diagnosis_code"]
NUMERIC_FEATURES = [
    "patient_age", "billed_amount",
    "days_since_last_claim", "num_prior_claims", "prior_denial_rate",
]
TARGET = "claim_status"


def load_and_prepare(path: Path):
    print(f"Loading data from: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}  |  Denial rate: {df[TARGET].mean():.2%}")

    # Drop columns not used as features
    drop_cols = ["patient_id", "date", "anomaly_label", TARGET]
    X_raw = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df[TARGET]

    # One-hot encode categoricals (same logic as denial_predictor.prepare_features)
    X_encoded = pd.get_dummies(X_raw, columns=CATEGORICAL_FEATURES, drop_first=True)

    print(f"  Features after encoding: {X_encoded.shape[1]}")
    return X_encoded, y


CANDIDATES = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=200, learning_rate=0.05,
                                                       max_depth=4, random_state=42),
}


def evaluate(name, model, X_train, X_test, y_train, y_test, scaler):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    # IMPORTANT: use predict_proba scores (not hard labels) for AUC
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_proba), 4),   # ← probabilities
    }
    print(f"  {name:<22}  AUC={metrics['roc_auc']:.4f}  "
          f"F1={metrics['f1_score']:.4f}  Acc={metrics['accuracy']:.4f}")
    return metrics


def main():
    X, y = load_and_prepare(DATA_PATH)
    feature_names = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print("\nComparing models (AUC uses probability scores):")
    results = {}
    trained_models = {}
    for name, clf in CANDIDATES.items():
        metrics = evaluate(name, clf, X_train_s, X_test_s, y_train, y_test, scaler)
        results[name] = metrics
        trained_models[name] = clf

    # Pick best by ROC-AUC
    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best_model = trained_models[best_name]
    best_metrics = results[best_name]
    print(f"\nBest model: {best_name}  (AUC {best_metrics['roc_auc']:.4f})")

    if best_metrics["roc_auc"] < 0.70:
        print("WARNING: AUC below 0.70 — check data quality or feature engineering.")

    # Feature importance for top_features list
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
    else:
        importances = np.abs(best_model.coef_[0])

    top_features = [
        feature_names[i]
        for i in np.argsort(importances)[::-1][:10]
    ]

    joblib.dump(best_model, SAVE_DIR / "denial_model.pkl")
    joblib.dump(scaler,     SAVE_DIR / "denial_model_scaler.pkl")
    joblib.dump(feature_names, SAVE_DIR / "denial_model_features.pkl")

    metadata = {
        "model_type":    best_name,
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_size":  len(X),
        "train_size":    len(X_train),
        "test_size":     len(X_test),
        "numeric_features": len(feature_names),   
        "metrics":       best_metrics,
        "top_features":  top_features,
        "all_model_results": results,            
    }

    with open(SAVE_DIR / "denial_model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"\nArtifacts saved to: {SAVE_DIR}")
    print(f"  denial_model.pkl          ({best_name})")
    print(f"  denial_model_scaler.pkl")
    print(f"  denial_model_features.pkl ({len(feature_names)} features)")
    print(f"  denial_model_metadata.json")
    print(f"\nClassification Report ({best_name}):")
    y_pred_best = best_model.predict(X_test_s)
    print(classification_report(y_test, y_pred_best))


if __name__ == "__main__":
    main()