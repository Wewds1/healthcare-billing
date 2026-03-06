from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def get_patient(db: Session, patient_id: int):
    # Single Patient Query using ID
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100):
    # Get all patient Pagination
    return db.query(Patient).offset(skip).limit(limit).all()


def create_patient(db: Session, patient: PatientCreate):
    # Create new Patient
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient



def update_patient(db: Session, patient_id: int, patient: PatientUpdate):
    # update existing patient
    db_patient = get_patient(db, patient_id)
    if db_patient:
        update_data = patient.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_patient, key, value)

        db.commit()
        db.refresh(db_patient)

    return db_patient


def delete_patient(db: Session, patient_id: int):
    # delete patient 
    db_patient = get_patient(db, patient_id)
    if db_patient:
        db.delete(db_patient)
        db.commit()

    return db_patient