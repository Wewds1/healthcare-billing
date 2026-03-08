import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.crud import user, patient, procedure, billing_record
from app.schemas.user import UserCreate
from app.schemas.patient import PatientCreate
from app.schemas.procedure import ProcedureCreate
from app.schemas.billing_record import BillingRecordCreate



def send_database():
    db = SessionLocal()
    
    try:
        print("Sending Data")


        users_data = [

            {
                'username': 'admin', 
                "email": "admin@admin.com",
                "role": "admin",
                "password": "adminadmin"
             },  
             
             {
                "username": "doctor1", 
                "email": "doctor1@hospital.com", 
                "role": "user",
                "password": "Doctor123!"
            },

            {
                "username": "billing_staff",
                "email": "billing@hospital.com", 
                "role": "user", 
                "password": "Staff123!"
            },
        ]

        created_users = []
        for user_data in users_data:
            existing = user.get_user_by_username(db, user_data["username"])
            if not existing:
                created_user = user.create_user(db, UserCreate(**user_data))
                created_users.append(created_user)
                print(f"Created user: {created_user.username}")
            else:
                print(f"User already exists: {existing.username}")

        print("creating procedures")
        procedures_data = [
            {"cpt_code": "99213", "description": "Office Visit - Established Patient (15 min)", "price": 150},
            {"cpt_code": "99214", "description": "Office Visit - Established Patient (25 min)", "price": 200},
            {"cpt_code": "80053", "description": "Comprehensive Metabolic Panel", "price": 75},
            {"cpt_code": "85025", "description": "Complete Blood Count (CBC)", "price": 45},
            {"cpt_code": "93000", "description": "Electrocardiogram (EKG)", "price": 125},
        ]


    finally:
        db.close()