from sqlalchemy.orm import Session
from app.models.billing_record import BillingRecord
from app.schemas.billing_record import BillingRecordCreate, BillingRecordUpdate



def get_billing_record(db: Session, billing_record_id: int):
    # get a single billing record by id
    return db.query(BillingRecord).filter(BillingRecord.id == billing_record_id).first()


def get_billing_records(db: Session, skip: int = 0, limit: int = 100):
    # get all billing records with pagination
    return db.query(BillingRecord).offset(skip).limit(limit).all()



def get_billing_records_by_patient_id(db: Session, patient_id: int):
    # get billing records by patient id
    return db.query(BillingRecord).filter(BillingRecord.patient_id == patient_id).all()


def get_billing_records_by_status(db: Session, status: str):
    # get billing records by status
    return db.query(BillingRecord).filter(BillingRecord.status == status).all()


def create_billing_record(db: Session, billing_record: BillingRecordCreate):
    # create a new billing record
    db_billing_record = BillingRecord(**billing_record.model_dump())
    db.add(db_billing_record)
    db.commit()
    db.refresh(db_billing_record)
    return db_billing_record

def update_billing_record(db: Session, billing_record_id: int, billing_record: BillingRecordUpdate):
    # update existing billing record
    db_billing_record = get_billing_record(db, billing_record_id)
    if db_billing_record:
        update_data = billing_record.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_billing_record, key, value)

        db.commit()
        db.refresh(db_billing_record)
    return db_billing_record


def delete_billing_record(db: Session, billing_record_id: int):
    # delete a billing record
    db_billing_record = get_billing_record(db, billing_record_id)
    if db_billing_record:
        db.delete(db_billing_record)
        db.commit()
    return db_billing_record
