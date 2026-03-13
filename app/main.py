from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import user, patient, procedure, billing_record, auth, ml_predict
import os

app = FastAPI(
    title="Healthcare Billing System",
    description="Backend API for managing patients, procedures, and billing records",
    version="1.0.1"
)

# Environment-based CORS (more secure)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:8501,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(patient.router)
app.include_router(procedure.router)
app.include_router(billing_record.router)
app.include_router(ml_predict.router)


@app.get("/")
def read_root():
    return {
        "message": "Healthcare Billing API is running",
        "version": "1.0.1",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected", "ml_enabled": True}