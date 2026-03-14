from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


from app.core.dependencies import get_db
from app.core.rbac import require_role, require_user
from ml.inference.denial_predictor import get_predictor, DenialPredictor


router = APIRouter(prefix="/ml", tags=["ml-prediction"])

class PredictionInput(BaseModel): 
    # Schema for single Prediction
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
    feature : str
    importance : float
    
    
class ModelInfo(BaseModel):
    model_type: str
    training_date: str # double check if this match on denial_predictor.py
    training_data_size: int
    num_features: int
    metrics: Dict
    top_features: List[str]
    
    
    
    
@router.post("/predict/denial", response_model=PredictionOutput, status_code=200)
async def predict_denial(input_data: PredictionInput, current_user = Depends(require_user)):
    """ Predict claim probability for single claim
    
        requires admin 
        
        returns predicted probability of claim denial, risk level, and top risk factors
    """
    
    try:
        predictor = get_predictor()
        
        input_dict = input_data.dict()
        result = predictor.predict(input_dict)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.post("/predict/denial/batch", response_model=BatchPredictionOutput, status_code=200)
async def batch_predict_denial(batch_input: BatchPredictionInput, current_user = Depends(require_user)):
    """ Predict claim probability for batch of claims
    
        requires admin 
        
        returns list of predictions and summary statistics for the batch
    """
    
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
    # ill probably dont need this but well lets just add can be refactored later on
    try:
        predictor = get_predictor()
        model_info = predictor.get_model_info()
        return model_info

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
@router.get("/model/feature-importance", response_model=List[FeatureImportance], status_code=200)
async def get_feature_importance(current_user = Depends(require_user)):
    
    try:
        predictor = get_predictor()
        feature_importances = predictor.get_feature_importance()
        return feature_importances
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.get("/health", status_code=200)
async def ml_health_check():
    try:
        predictor = get_predictor()
        model_info = predictor.get_model_info()
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_type": model_info['model_type'],
            "message": "ML prediction service is operational"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "error": str(e),
            "message": "ML model failed to load"
        }
        

