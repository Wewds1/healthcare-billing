from sqlalchemy import Integer, String, Column
from app.database import Base


class ScriptLog(Base):
    __tablename__ = 'script_logs'
    id = Column(Integer, primary_key=True, index=True)
    script_name = Column(String)
    status = Column(String)  # e.g., 'success', 'failure'
    message = Column(String)  # Detailed log message


