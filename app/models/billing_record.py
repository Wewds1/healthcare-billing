from sqlalchemy import Integer, String, Column, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"))

    procedure_id = Column(Integer, ForeignKey("procedures.id"))

    amount = Column(Float)

    date = Column(DateTime, default=func.now())

    status = Column(String)