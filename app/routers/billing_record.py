from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime

from app.core.dependencies import get_db
from app.schemas.billing_record import BillingRecord, BillingRecordCreate, BillingRecordUpdate
from app.crud import billing_record as crud
from app.crud import patient as patient_crud
from app.crud import procedure as procedure_crud
from app.core.rbac import require_admin, require_user
from ml.inference.anomaly_detector import get_anomaly_detector

router = APIRouter(prefix="/billing", tags=["billing"])

"""
User can read billing records but only admin can create, update and delete.
Auto-scan for anomalies on creation.
"""


VALID_DIAGNOSIS_PROCEDURE_PAIRS = {
    "J06.9": {"99213", "99214", "36415", "87070"},
    "E11.9": {"99213", "99214", "82947", "80053"},
    "I10": {"99213", "99214", "93000", "80053"},
    "M79.3": {"99213", "99214", "97110", "96372"},
    "R51": {"99213", "99214", "70450"},
    "J44.9": {"99214", "99215", "71020", "93000"},
    "K21.9": {"99213", "80053"},
    "E78.5": {"99213", "80061"},
    "M25.5": {"99213", "73610", "97110"},
    "R10.9": {"99213", "99214", "80053"},
    "F41.9": {"99213", "99214"},
    "S93.4": {"99282", "99283", "73610", "96372"},
    "J02.9": {"99213", "87070"},
    "N39.0": {"99213", "87070", "80053"},
    "Z00.00": {"99213", "99214", "85025", "80053"},
}


def calculate_age(date_of_birth: str | None) -> int:
    if not date_of_birth:
        return 0

    try:
        birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        return 0

    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


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
        patient = patient_crud.get_patient(db, patient_id=record.patient_id)
        procedure = procedure_crud.get_procedure(db, procedure_id=record.procedure_id)
        patient_claim_history = crud.get_billing_records_by_patient_id(db, patient_id=record.patient_id)
        prior_claims = [claim for claim in patient_claim_history if claim.id != db_billing_record.id]
        denied_claims = [claim for claim in prior_claims if claim.status == "denied"]

        latest_prior_claim = max(prior_claims, key=lambda claim: claim.date) if prior_claims else None
        days_since_last_claim = 999
        if latest_prior_claim and latest_prior_claim.date:
            last_claim_date = latest_prior_claim.date.date() if hasattr(latest_prior_claim.date, "date") else latest_prior_claim.date
            days_since_last_claim = max((date.today() - last_claim_date).days, 0)

        diagnosis_code = (record.diagnosis_code or "").upper()
        procedure_code = procedure.cpt_code if procedure else ""

        anomaly_input = {
            "patient_age": calculate_age(patient.date_of_birth if patient else None),
            "billed_amount": db_billing_record.amount,
            "days_since_last_claim": days_since_last_claim,
            "num_prior_claims": len(prior_claims),
            "prior_denial_rate": round(len(denied_claims) / max(len(prior_claims), 1), 3),
            "is_code_mismatch": int(
                bool(diagnosis_code and procedure_code)
                and procedure_code not in VALID_DIAGNOSIS_PROCEDURE_PAIRS.get(diagnosis_code, {procedure_code})
            ),
            "is_high_cost_procedure": int(bool(procedure and procedure.price >= 500)),
            "is_frequent_claimer": int(len(prior_claims) > 3 and days_since_last_claim < 30),
            "is_recent_repeat_claim": int(days_since_last_claim < 7),
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
