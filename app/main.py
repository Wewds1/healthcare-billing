from fastapi import FastAPI
from app.database import engine, Base
from app.routers import user, patient, procedure, billing_record


app = FastAPI(
    title="Healthcare Billing System",
    description="Backend API for managing patients, procedures, and billing records",
    version="1.0.0"
)

app.include_router(user.router)
app.include_router(patient.router)
app.include_router(procedure.router)
app.include_router(billing_record.router)


@app.get("/")
def read_root():
    return {
        "message": "Healthcare Billing API is running",
        "docs": "/docs",
        "redoc": "/redoc"
    }