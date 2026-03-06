from sqlalchemy.orm import Session
from app.models.procedure import Procedure
from app.schemas import ProcedureCreate, ProcedureUpdate



def get_procedure(db: Session, procedure_id: int):
    # this is just a single procedure for example
    return db.query(Procedure).filter(Procedure.id == procedure_id).first()


def get_procedures(db: Session, skip: int = 0, limit: int = 100):
    # get all the procedures with pagination
    return db.query(Procedure).offset(skip).limit(limit).all()


def get_procedure_by_cpt_code(db: Session, cpt_code: str):
    # get a procedure by its CPT code
    return db.query(Procedure).filter(Procedure.cpt_code == cpt_code).first()



def create_procedure(db: Session, procedure: ProcedureCreate):
    # create a new procedure
    db_procedure = Procedure(**procedure.model_dump())
    db.add(db_procedure)
    db.commit()
    db.refresh(db_procedure)
    return db_procedure


def update_procedure(db: Session, procedure_id: int, procedure: ProcedureUpdate):
    # update existing procedure
    db_procedure = get_procedure(db, procedure_id)
    if db_procedure:
        update_data = procedure.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_procedure, key, value)

        db.commit()
        db.refresh(db_procedure)
    return db_procedure


def delete_procedure(db: Session, procedure_id: int):
    # delete a procedure
    db_procedure = get_procedure(db, procedure_id)
    if db_procedure:
        db.delete(db_procedure)
        db.commit()
    return db_procedure
