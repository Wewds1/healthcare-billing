from fastapi import FastAPI
from app.database import engine, Base

app = FastAPI()

# just test db tables
@app.get("/")
def read_root():
    return {"message": "API is running"}