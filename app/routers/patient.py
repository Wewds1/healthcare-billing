from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.patient import Patient, PatientCreate, PatientUpdate
from app.crud import patient as crud
from app.core.rbac import require_admin, require_user


router = APIRouter(prefix="/patients", tags=["patients"])

"""
User can read patient information but only admin can create, update and delete patient for now but can be adjusted with doctor role in the future
"""

# get all patients
@router.get("/", response_model=List[Patient])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(require_user)):
    patients = crud.get_patients(db, skip=skip, limit=limit)
    return patients

# get patient by id
@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user = Depends(require_user)):
    patient = crud.get_patient(db, patient_id=patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

#create new patient
@router.post("/", response_model=Patient)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    return crud.create_patient(db, patient=patient)


#update patient by id
@router.put("/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, patient: PatientUpdate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return crud.update_patient(db, patient_id=patient_id, patient=patient)


# delete patient by id
@router.delete("/{patient_id}", response_model=Patient)
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_patient = crud.delete_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient



