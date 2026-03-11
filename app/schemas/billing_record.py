from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class BillingRecordBase(BaseModel):
    patient_id : int 
    procedure_id : int
    amount : float
    status : str
    diagnosis_code : Optional[str] = None


class BillingRecordCreate(BillingRecordBase):
    pass


class BillingRecordUpdate(BaseModel):
    patient_id : Optional[int] = None
    procedure_id : Optional[int] = None
    amount : Optional[float] = None
    status : Optional[str]  = None
    diagnosis_code : Optional[str] = None


class BillingRecord(BillingRecordBase):
    id : int
    date : datetime
    anomaly_score : Optional[float] = None
    is_flagged : Optional[bool] = None

    class Config:
        from_attributes = True