from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.procedure import Procedure, ProcedureCreate, ProcedureUpdate
from app.crud import procedure as crud
from app.core.rbac import require_admin, require_user, get_current_user



router = APIRouter(prefix="/procedures", tags=["procedures"])


"""
All user can read procedure but only admin can create, update and delete procedure for now but can be adjusted with doctor role in the future

"""

# Get all procedures with pagination can be read by user
@router.get("/", response_model=List[Procedure])
def read_procedures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(require_user)):
    procedures = crud.get_procedures(db, skip=skip, limit=limit)
    return procedures


#get procedure by id can be read by user
@router.get("/{procedure_id}", response_model=Procedure)
def read_procedure(procedure_id: int, db: Session = Depends(get_db), current_user=Depends(require_user)):
    procedure = crud.get_procedure(db, procedure_id=procedure_id)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return procedure


# Create new Procedure -- only admin can create procedure but can be adjusted with doctor role in the future
@router.post("/", response_model=Procedure)
def create_procedure(procedure: ProcedureCreate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_procedure = crud.get_procedure_by_cpt_code(db, cpt_code=procedure.cpt_code)
    if db_procedure:
        raise HTTPException(status_code=400, detail="Procedure with this CPT code already exists")
    return crud.create_procedure(db, procedure=procedure)

# update existing procedure for now its just admin 
@router.put("/{procedure_id}", response_model=Procedure)
def update_procedure(procedure_id: int, procedure: ProcedureUpdate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_procedure = crud.get_procedure(db, procedure_id=procedure_id)
    if db_procedure is None:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return db_procedure 

# delete a procedure
@router.delete("/{procedure_id}", response_model=Procedure)
def delete_procedure(procedure_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_procedure = crud.delete_procedure(db, procedure_id=procedure_id)
    if db_procedure is None:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return db_procedure