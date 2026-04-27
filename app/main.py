from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text

from app import models  # noqa: F401 - registers SQLAlchemy models
from app.database import Base, engine
from app.routers import auth, billing_record, ml_predict, ocr, patient, procedure, user


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Healthcare Billing System",
    description="Backend API for managing patients, procedures, and billing records",
    version="1.1.0",
    lifespan=lifespan,
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
app.include_router(ocr.router)


@app.get("/")
def read_root():
    return {
        "message": "Healthcare Billing API is running",
        "version": "1.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    db_status = "connected"
    ml_status = {"denial_model_loaded": False, "anomaly_model_loaded": False}
    errors = []

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "unavailable"
        errors.append(f"database: {exc}")

    try:
        from ml.inference.anomaly_detector import get_anomaly_detector
        from ml.inference.denial_predictor import get_predictor

        get_predictor()
        get_anomaly_detector()
        ml_status = {"denial_model_loaded": True, "anomaly_model_loaded": True}
    except Exception as exc:
        errors.append(f"ml: {exc}")

    overall = "healthy" if db_status == "connected" and not errors else "degraded"
    return {
        "status": overall,
        "database": db_status,
        "ml": ml_status,
        "version": "1.1.0",
        "errors": errors,
    }
