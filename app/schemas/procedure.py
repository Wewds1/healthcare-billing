from pydantic import BaseModel
from typing import Optional



class ProcedureBase(BaseModel):
    cpt_code : str
    description : str
    price: int 



class ProcedureCreate(ProcedureBase):
    pass



class ProcedureUpdate(BaseModel):
    cpt_code : Optional[str] = None
    description : Optional[str] = None
    price: Optional[int] = None



class Procedure(ProcedureBase):
    id : int

    class Config:
        from_attributes = True