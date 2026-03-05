from pydantic import BaseModel
from typing import Optional


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    insurance_provider: str


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    insurance_provider: Optional[str] = None


class Patient(PatientBase):
    id: int

    class Config:
        from_attributes = True