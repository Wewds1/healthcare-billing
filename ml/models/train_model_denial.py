import json
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder


ROOT = Path(__file__).parent.parent.parent
DATA_PATH = ROOT / "ml" / "data" / "synthetic_billin.csv"
SAVE_DIR = ROOT / "ml" / "models" / "saved"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


CATEGORICAL_FEATURES = ["insurance_type", "procedure_cpt_code", "diagnosis_code"]
NUMERIC_FEATURES = [
    "patient_age", "billed_amount",
    "days_since_last_claim", "num_prior_claims", "prior_denial_rate",
]
TARGET = "claim_status"


CANDIDATES = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=-1),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, random_state=42, max_depth=4)
}


def load_and_prepare(path: Path):
    print(f"Loading data from {path}...")
    df = pd.read_csv(path)
    print(f"Shape: {df.shape} | Denial Rate: {df[TARGET].mean():.2%}")
    
    drop_cols = ['patient_id', 'date', 'anomaly_label', TARGET]
    
    X_raw = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df[TARGET]
    X_encoded = pd.get_dummies(X_raw, columns=CATEGORICAL_FEATURES, drop_first=True)
    print(f"After encoding: {X_encoded.shape} | Features: {X_encoded.columns.tolist()}")
    
    return X_encoded, y

    
    

def evaluate(name, model, X_train, X_test, y_train, y_test, scaler):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    y_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred),4),
        "precision": round(precision_score(y_test, y_pred),4),
        "recall": round(recall_score(y_test, y_pred),4),
        "f1_score": round(f1_score(y_test, y_pred),4),
        "roc_auc": round(roc_auc_score(y_test, y_proba),4)
    }
    
    print(f"{name} Metrics: {metrics}")
    
    return metrics



def main():
    X, y = load_and_prepare(DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)