from sqlalchemy import Column, Integer, String 
from app.database import Base


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    cpt_code = Column(String, unique=True)
    description = Column(String)
    price = Column(Integer)

    