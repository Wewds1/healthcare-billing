from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import user, patient, procedure, billing_record, auth  

app = FastAPI(
    title="Healthcare Billing System",
    description="Backend API for managing patients, procedures, and billing records",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(patient.router)
app.include_router(procedure.router)
app.include_router(billing_record.router)


@app.get("/")
def read_root():
    return {
        "message": "Healthcare Billing API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}