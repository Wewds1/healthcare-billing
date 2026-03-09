from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.billing_record import BillingRecord, BillingRecordCreate, BillingRecordUpdate
from app.crud import billing_record as crud

router = APIRouter(prefix="/billing", tags=["billing"])


# Get all billing records with pagination
@router.get("/", response_model=List[BillingRecord])
def read_billing_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    records = crud.get_billing_records(db, skip=skip, limit=limit)
    return records


# get billing record by id
@router.get("/{record_id}", response_model=BillingRecord)
def read_billing_record(record_id: int, db: Session = Depends(get_db)):
    db_record = crud.get_billing_record(db, billing_record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record


# get patient billing records by patient id
@router.get("/patient/{patient_id}", response_model=List[BillingRecord])
def read_billing_records_by_patient(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_billing_records_by_patient_id(db, patient_id=patient_id)


# Get billing records by status
@router.get("/status/{status}", response_model=List[BillingRecord])
def read_billing_records_by_status(status: str, db: Session = Depends(get_db)):
    return crud.get_billing_records_by_status(db, status=status)


# Create a new billing record
@router.post("/", response_model=BillingRecord, status_code=201)
def create_billing_record(record: BillingRecordCreate, db: Session = Depends(get_db)):
    return crud.create_billing_record(db=db, billing_record=record)


#update billing record by id
@router.put("/{record_id}", response_model=BillingRecord)
def update_billing_record(record_id: int, record: BillingRecordUpdate, db: Session = Depends(get_db)):
    db_record = crud.update_billing_record(db, billing_record_id=record_id, billing_record=record)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record


#delete billing record by id
@router.delete("/{record_id}", response_model=BillingRecord)
def delete_billing_record(record_id: int, db: Session = Depends(get_db)):
    db_record = crud.delete_billing_record(db, billing_record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Billing record not found")
    return db_record