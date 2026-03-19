from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.billing_record import BillingRecord, BillingRecordCreate, BillingRecordUpdate
from app.crud import billing_record as crud
from app.core.rbac import require_admin, require_user
from ml.inference.anomaly_detector import get_anomaly_detector

router = APIRouter(prefix="/billing", tags=["billing"])

"""
User can read billing records but only admin can create, update and delete.
Auto-scan for anomalies on creation.
"""


@router.get("/", response_model=List[BillingRecord])
def read_billing_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(require_user)):
    """Get all billing records with pagination."""
    records = crud.get_billing_records(db, skip=skip, limit=limit)
    return records


@router.get("/{record_id}", response_model=BillingRecord)
def read_billing_record(record_id: int, db: Session = Depends(get_db), current_user=Depends(require_user)):
    """Get a single billing record by ID."""
    db_record = crud.get_billing_record(db, billing_record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record


@router.get("/patient/{patient_id}", response_model=List[BillingRecord])
def read_billing_records_by_patient(patient_id: int, db: Session = Depends(get_db), current_user = Depends(require_user)):
    """Get billing records for a specific patient."""
    return crud.get_billing_records_by_patient_id(db, patient_id=patient_id)


@router.get("/status/{status}", response_model=List[BillingRecord])
def read_billing_records_by_status(status: str, db: Session = Depends(get_db), current_user = Depends(require_user)):
    """Get billing records by status."""
    return crud.get_billing_records_by_status(db, status=status)


@router.post("/", response_model=BillingRecord, status_code=201)
def create_billing_record(record: BillingRecordCreate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Create a new billing record with automatic anomaly scan."""
    # Create the record first
    db_billing_record = crud.create_billing_record(db=db, billing_record=record)
    
    # Run anomaly detection (use defaults for engineered flags not yet captured)
    try:
        detector = get_anomaly_detector()
        anomaly_input = {
            "patient_age": 65,  # placeholder, would come from patient join
            "billed_amount": db_billing_record.amount,
            "days_since_last_claim": 45,  # placeholder
            "num_prior_claims": 0,  # placeholder
            "prior_denial_rate": 0.0,  # placeholder
            "is_code_mismatch": 0,
            "is_high_cost_procedure": 0,
            "is_frequent_claimer": 0,
            "is_recent_repeat_claim": 0,
        }
        
        anomaly_result = detector.predict(anomaly_input)
        
        # Update record with anomaly scan results
        db_billing_record.anomaly_score = anomaly_result.get("anomaly_score", None)
        db_billing_record.is_flagged = anomaly_result.get("is_flagged", False)
        
        db.commit()
        db.refresh(db_billing_record)
        
    except Exception as e:
        # Log error but don't fail the request if anomaly detection fails
        print(f"Warning: Anomaly detection failed: {str(e)}")
        # Record created successfully; anomaly flags remain as defaults
    
    return db_billing_record


@router.put("/{record_id}", response_model=BillingRecord)
def update_billing_record(record_id: int, record: BillingRecordUpdate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Update a billing record by ID."""
    db_record = crud.update_billing_record(db, billing_record_id=record_id, billing_record=record)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record


@router.delete("/{record_id}", response_model=BillingRecord)
def delete_billing_record(record_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Delete a billing record by ID."""
    db_record = crud.delete_billing_record(db, billing_record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record