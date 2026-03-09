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

        print("creating procedures") # verification print 
        procedures_data = [
            {"cpt_code": "99213", "description": "Office Visit - Established Patient (15 min)", "price": 150},
            {"cpt_code": "99214", "description": "Office Visit - Established Patient (25 min)", "price": 200},
            {"cpt_code": "80053", "description": "Comprehensive Metabolic Panel", "price": 75},
            {"cpt_code": "85025", "description": "Complete Blood Count (CBC)", "price": 45},
            {"cpt_code": "93000", "description": "Electrocardiogram (EKG)", "price": 125},
        ]

        created_procedures = []
        for procedure_data in procedures_data:
            existing = procedure.get_procedure_by_cpt_code(db, procedure_data["cpt_code"])
            if not existing:
                created_procedure = procedure.create_procedure(db, ProcedureCreate(**procedure_data))
                created_procedures.append(created_procedure)
                print(f"Created procedure: {created_procedure.cpt_code}")
            else:
                print(f"Procedure already exists: {existing.cpt_code}")


        print("Creating Patients")
        patients_data = [
            {"first_name": "John", "last_name": "Doe", "date_of_birth": "1980-05-15", "insurance_provider": "Blue Cross Blue Shield"},
            {"first_name": "Jane", "last_name": "Smith", "date_of_birth": "1992-08-22", "insurance_provider": "Aetna"},
            {"first_name": "Michael", "last_name": "Johnson", "date_of_birth": "1975-12-03", "insurance_provider": "UnitedHealthcare"},
            {"first_name": "Emily", "last_name": "Williams", "date_of_birth": "1988-03-17", "insurance_provider": "Cigna"},
            {"first_name": "Robert", "last_name": "Brown", "date_of_birth": "1965-11-28", "insurance_provider": "Medicare"},
        ]

        created_patients = []
        for patient_data in patients_data:
            created_patient = patient.create_patient(db, PatientCreate(**patient_data))
            created_patients.append(created_patient)
            print(f" Created patient: {created_patient.first_name} {created_patient.last_name}")

        
        print("Creating billing records")
        billing_data = [
            {"patient_id": created_patients[0].id, "procedure_id": created_procedures[0].id, "amount": 150.00, "status": "paid"},
            {"patient_id": created_patients[0].id, "procedure_id": created_procedures[2].id, "amount": 75.00, "status": "paid"},
            {"patient_id": created_patients[1].id, "procedure_id": created_procedures[1].id, "amount": 200.00, "status": "pending"},
            {"patient_id": created_patients[2].id, "procedure_id": created_procedures[3].id, "amount": 45.00, "status": "paid"},
            {"patient_id": created_patients[2].id, "procedure_id": created_procedures[4].id, "amount": 125.00, "status": "denied"},
            {"patient_id": created_patients[3].id, "procedure_id": created_procedures[0].id, "amount": 150.00, "status": "pending"},
            {"patient_id": created_patients[4].id, "procedure_id": created_procedures[1].id, "amount": 200.00, "status": "paid"},
        ]


        for bill_data in billing_data:
            created_bill = billing_record.create_billing_record(db, BillingRecordCreate(**bill_data))
            print(f"Created billing record id: {created_bill.id} - {created_bill.amount} ({created_bill.status})")
   

        print(f"   Users: {len(created_users)}")
        print(f"   Procedures: {len(created_procedures)}")
        print(f"   Patients: {len(created_patients)}")
        print(f"   Billing Records: {len(billing_data)}")



    except Exception as e:
        print("error database seed")
        db.rollback()

        
    finally:
        db.close()


if __name__ ==  "__main__":
    send_database()