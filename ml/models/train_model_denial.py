import json
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

CATEGORICAL_FEATURES = [
    "insurance_type",
    "procedure_cpt_code",
    "diagnosis_code",
    "place_of_service",
    "claim_type",
    "network_status",
]
NUMERIC_FEATURES = [
    "patient_age",
    "billed_amount",
    "days_since_last_claim",
    "num_prior_claims",
    "prior_denial_rate",
    "authorization_required",
    "authorization_on_file",
    "units",
    "is_code_mismatch",
    "is_high_cost_procedure",
    "is_frequent_claimer",
    "is_recent_repeat_claim",
]
TARGET = "claim_status"

CANDIDATES = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        random_state=42,
    ),
}


def load_and_prepare(path: Path):
    print(f"Loading data from: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}  |  Denial rate: {df[TARGET].mean():.2%}")

    X_raw = df.drop(columns=["patient_id", "date", "anomaly_label", TARGET], errors="ignore")
    y = df[TARGET]
    X_encoded = pd.get_dummies(X_raw, columns=CATEGORICAL_FEATURES, drop_first=True)
    ordered_features = NUMERIC_FEATURES + [column for column in X_encoded.columns if column not in NUMERIC_FEATURES]
    X_encoded = X_encoded[ordered_features]

    print(f"  Features after encoding: {X_encoded.shape[1]}")
    return X_encoded, y


def select_threshold(y_true, y_proba):
    best_threshold = 0.5
    best_f1 = -1.0

    for threshold in np.arange(0.25, 0.76, 0.01):
        y_pred = (y_proba >= threshold).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_f1:
            best_threshold = round(float(threshold), 2)
            best_f1 = score

    return best_threshold, round(float(best_f1), 4)


def evaluate(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    threshold, threshold_f1 = select_threshold(y_test, y_proba)
    y_pred = (y_proba >= threshold).astype(int)

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "chosen_threshold": threshold,
        "threshold_f1": threshold_f1,
    }
    print(f"  {name:<22}  AUC={metrics['roc_auc']:.4f}  F1={metrics['f1_score']:.4f}  Acc={metrics['accuracy']:.4f}")
    return metrics


def main():
    X, y = load_and_prepare(DATA_PATH)
    feature_names = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("\nComparing models:")
    results = {}
    trained_models = {}
    for name, clf in CANDIDATES.items():
        results[name] = evaluate(name, clf, X_train_s, X_test_s, y_train, y_test)
        trained_models[name] = clf

    best_name = max(results, key=lambda candidate: results[candidate]["roc_auc"])
    best_model = trained_models[best_name]
    best_metrics = results[best_name]
    print(f"\nBest model: {best_name} (AUC {best_metrics['roc_auc']:.4f})")

    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
    else:
        importances = np.abs(best_model.coef_[0])

    top_features = [feature_names[i] for i in np.argsort(importances)[::-1][:10]]

    joblib.dump(best_model, SAVE_DIR / "denial_model.pkl")
    joblib.dump(scaler, SAVE_DIR / "denial_model_scaler.pkl")
    joblib.dump(feature_names, SAVE_DIR / "denial_model_features.pkl")

    metadata = {
        "model_type": best_name,
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_size": len(X),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "num_features": len(feature_names),
        "metrics": best_metrics,
        "top_features": top_features,
        "all_model_results": results,
        "chosen_threshold": best_metrics["chosen_threshold"],
    }

    with open(SAVE_DIR / "denial_model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"\nArtifacts saved to: {SAVE_DIR}")
    y_pred_best = (best_model.predict_proba(X_test_s)[:, 1] >= best_metrics["chosen_threshold"]).astype(int)
    print(f"\nClassification Report ({best_name}):")
    print(classification_report(y_test, y_pred_best))


if __name__ == "__main__":
    main()
