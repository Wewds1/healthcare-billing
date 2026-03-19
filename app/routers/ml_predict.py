from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


from app.core.dependencies import get_db
from app.core.rbac import require_user
from ml.inference.denial_predictor import get_predictor, DenialPredictor
from ml.inference.anomaly_detector import get_anomaly_detector, AnomalyDetector


router = APIRouter(prefix="/ml", tags=["ml-prediction"])


class PredictionInput(BaseModel): 
    """Schema for single denial prediction."""
    patient_age: int = Field(..., ge=0, le=120, description="Age of the patient in years")
    insurance_type: str = Field(..., description="Type of insurance (e.g., 'Medicare', 'Private')")
    procedure_cpt_code: str = Field(..., description="CPT code for the medical procedure")
    diagnosis_code: str = Field(..., description="ICD-10 code for the diagnosis")
    billed_amount: float = Field(..., gt=0, description="Billed amount")
    days_since_last_claim: int = Field(..., ge=0, description="Days since patient's last claim")
    num_prior_claims: int = Field(..., ge=0, description="Number of prior claims")
    prior_denial_rate: float = Field(..., ge=0, le=1, description="Historical denial rate (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "patient_age": 65,
                "insurance_type": "Medicare",
                "procedure_cpt_code": "99214",
                "diagnosis_code": "E11.9",
                "billed_amount": 250.00,
                "days_since_last_claim": 45,
                "num_prior_claims": 3,
                "prior_denial_rate": 0.33
            }
        }


class PredictionOutput(BaseModel):
    """Denial prediction output."""
    denial_probability: float = Field(..., ge=0, le=1, description="Predicted probability of claim denial")
    risk_level: str = Field(..., description="Risk level (e.g., 'Low', 'Medium', 'High')")
    prediction: int = Field(..., description="Binary prediction (0 for Approved, 1 for Denied)")
    prediction_label: str = Field(..., description="Prediction label (e.g., 'Approved', 'Denied')")
    top_risk_factors: List[Dict] = Field(..., description="List of top risk factors with importance scores")


class BatchPredictionInput(BaseModel):
    claims: List[PredictionInput] = Field(..., description="List of claims for batch prediction")
    
    
class BatchPredictionOutput(BaseModel):
    predictions: List[PredictionOutput] = Field(..., description="List of predictions for each claim in the batch")
    summary: Dict = Field(..., description="Summary statistics for the batch predictions")
    
    
class FeatureImportance(BaseModel):
    feature: str
    importance: float
    
    
class ModelInfo(BaseModel):
    model_type: str
    training_date: str
    training_data_size: int
    num_features: int
    metrics: Dict
    top_features: List[str]



class AnomalyScanInput(BaseModel):
    """Schema for anomaly scan on a single record."""
    patient_age: int = Field(..., ge=0, le=120)
    billed_amount: float = Field(..., gt=0)
    days_since_last_claim: int = Field(..., ge=0)
    num_prior_claims: int = Field(..., ge=0)
    prior_denial_rate: float = Field(..., ge=0, le=1)
    is_code_mismatch: int = Field(default=0, ge=0, le=1)
    is_high_cost_procedure: int = Field(default=0, ge=0, le=1)
    is_frequent_claimer: int = Field(default=0, ge=0, le=1)
    is_recent_repeat_claim: int = Field(default=0, ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "patient_age": 65,
                "billed_amount": 1200.00,
                "days_since_last_claim": 5,
                "num_prior_claims": 8,
                "prior_denial_rate": 0.25,
                "is_code_mismatch": 0,
                "is_high_cost_procedure": 1,
                "is_frequent_claimer": 1,
                "is_recent_repeat_claim": 0
            }
        }


class AnomalyScanOutput(BaseModel):
    """Anomaly detection output."""
    isolation_prediction: int = Field(..., description="-1 (anomaly) or 1 (normal)")
    isolation_flag: int = Field(..., description="Binary flag from Isolation Forest")
    anomaly_score: float = Field(..., description="Raw anomaly score (lower = more anomalous)")
    rule_score: float = Field(..., description="Rule-based anomaly score")
    rule_reasons: List[str] = Field(..., description="List of triggered rule reasons")
    is_flagged: bool = Field(..., description="Final hybrid anomaly flag")
    risk_level: str = Field(..., description="Risk level: HIGH or LOW")


class AnomalyModelInfo(BaseModel):
    """Anomaly model metadata."""
    model_type: str
    training_date: str
    dataset_size: int
    features: List[str]
    contamination: float
    metrics: Dict
    rules: List[str]


@router.post("/predict/denial", response_model=PredictionOutput, status_code=200)
async def predict_denial(input_data: PredictionInput, current_user = Depends(require_user)):
    """Predict claim denial probability for a single claim."""
    try:
        predictor = get_predictor()
        input_dict = input_data.dict()
        result = predictor.predict(input_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/predict/denial/batch", response_model=BatchPredictionOutput, status_code=200)
async def batch_predict_denial(batch_input: BatchPredictionInput, current_user = Depends(require_user)):
    """Predict claim denial probability for a batch of claims."""
    try:
        predictor = get_predictor()
        input_dicts = [claim.dict() for claim in batch_input.claims]
        predictions = predictor.predict_batch(input_dicts)
        
        valid_predictions = [p for p in predictions if 'error' not in p]
        high_risk_count = sum(1 for p in valid_predictions if p['risk_level']== 'HIGH')
        medium_risk_count = sum(1 for p in valid_predictions if p['risk_level']== 'MEDIUM')
        low_risk_count = sum(1 for p in valid_predictions if p['risk_level']== 'LOW')
    
        avg_probability = sum(p['denial_probability'] for p in valid_predictions) / len(valid_predictions) if valid_predictions else 0
        
        summary = {
            'total_claims': len(batch_input.claims),
            'processed': len(valid_predictions),
            'high_risk': high_risk_count,
            'medium_risk': medium_risk_count,
            'low_risk': low_risk_count,
            'average_denial_probability': round(avg_probability, 4),
            'estimated_denials': sum(1 for p in valid_predictions if p['prediction'] == 1)
        }
        
        return {
            'predictions': predictions,
            'summary': summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    
@router.get("/model/info", response_model=ModelInfo, status_code=200)
async def get_model_info(current_user = Depends(require_user)):
    """Get denial prediction model metadata."""
    try:
        predictor = get_predictor()
        model_info = predictor.get_model_info()
        return model_info

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
@router.get("/model/feature-importance", response_model=List[FeatureImportance], status_code=200)
async def get_feature_importance(current_user = Depends(require_user)):
    """Get feature importance rankings for denial model."""
    try:
        predictor = get_predictor()
        feature_importances = predictor.get_feature_importance()
        return feature_importances
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.post("/anomalies/scan", response_model=AnomalyScanOutput, status_code=200)
async def scan_anomaly(input_data: AnomalyScanInput, current_user = Depends(require_user)):
    """Scan a record for anomalies using hybrid model."""
    try:
        detector = get_anomaly_detector()
        input_dict = input_data.dict()
        result = detector.predict(input_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/anomalies/model/info", response_model=AnomalyModelInfo, status_code=200)
async def get_anomaly_model_info(current_user = Depends(require_user)):
    """Get anomaly detection model metadata."""
    try:
        detector = get_anomaly_detector()
        model_info = detector.get_model_info()
        return model_info
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.get("/health", status_code=200)
async def ml_health_check():
    """Check ML service health."""
    try:
        predictor = get_predictor()
        detector = get_anomaly_detector()
        denial_info = predictor.get_model_info()
        anomaly_info = detector.get_model_info()
        
        return {
            "status": "healthy",
            "denial_model_loaded": True,
            "anomaly_model_loaded": True,
            "denial_model_type": denial_info['model_type'],
            "anomaly_model_type": anomaly_info['model_type'],
            "message": "ML prediction and anomaly detection services operational"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "ML services failed to initialize"
        }