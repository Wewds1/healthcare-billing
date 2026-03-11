import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.crud import user, patient, procedure, billing_record
from app.schemas.user import UserCreate
from app.schemas.patient import PatientCreate
from app.schemas.procedure import ProcedureCreate
from app.schemas.billing_record import BillingRecordCreate


def seed_database():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Starting Database Seeding...")
        print("=" * 60)

        # ==================== USERS ====================
        print("\n[1/4] Creating Users...")
        users_data = [
            {
                'username': 'admin', 
                "email": "admin@hospital.com",
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
                print(f"   ✅ Created user: {created_user.username} ({created_user.role})")
            else:
                created_users.append(existing)
                print(f"   ⚠️  User already exists: {existing.username}")

        # ==================== PROCEDURES ====================
        print("\n[2/4] Creating Procedures...")
        procedures_data = [
            {"cpt_code": "99213", "description": "Office Visit - Established Patient (15 min)", "price": 150},
            {"cpt_code": "99214", "description": "Office Visit - Established Patient (25 min)", "price": 200},
            {"cpt_code": "99215", "description": "Office Visit - Established Patient (40 min)", "price": 300},
            {"cpt_code": "80053", "description": "Comprehensive Metabolic Panel", "price": 75},
            {"cpt_code": "85025", "description": "Complete Blood Count (CBC)", "price": 45},
            {"cpt_code": "93000", "description": "Electrocardiogram (EKG)", "price": 125},
            {"cpt_code": "70450", "description": "CT Head without Contrast", "price": 650},
            {"cpt_code": "71020", "description": "Chest X-ray", "price": 150},
            {"cpt_code": "97110", "description": "Physical Therapy - Therapeutic Exercise", "price": 100},
            {"cpt_code": "96372", "description": "Therapeutic Injection", "price": 45},
        ]

        created_procedures = []
        for procedure_data in procedures_data:
            existing = procedure.get_procedure_by_cpt_code(db, procedure_data["cpt_code"])
            if not existing:
                created_procedure = procedure.create_procedure(db, ProcedureCreate(**procedure_data))
                created_procedures.append(created_procedure)
                print(f"   ✅ Created procedure: {created_procedure.cpt_code} - {created_procedure.description}")
            else:
                created_procedures.append(existing)
                print(f"   ⚠️  Procedure already exists: {existing.cpt_code}")

        # ==================== PATIENTS ====================
        print("\n[3/4] Creating Patients...")
        patients_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-05-15",
                "insurance_provider": "Blue Cross Blue Shield",
                "insurance_type": "Private",
                "email": "john.doe@email.com",
                "phone": "555-0101"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1992-08-22",
                "insurance_provider": "Aetna",
                "insurance_type": "Private",
                "email": "jane.smith@email.com",
                "phone": "555-0102"
            },
            {
                "first_name": "Michael",
                "last_name": "Johnson",
                "date_of_birth": "1975-12-03",
                "insurance_provider": "UnitedHealthcare",
                "insurance_type": "Private",
                "email": "michael.johnson@email.com",
                "phone": "555-0103"
            },
            {
                "first_name": "Emily",
                "last_name": "Williams",
                "date_of_birth": "1988-03-17",
                "insurance_provider": "Cigna",
                "insurance_type": "Private",
                "email": "emily.williams@email.com",
                "phone": "555-0104"
            },
            {
                "first_name": "Robert",
                "last_name": "Brown",
                "date_of_birth": "1965-11-28",
                "insurance_provider": "Medicare Part A",
                "insurance_type": "Medicare",
                "email": "robert.brown@email.com",
                "phone": "555-0105"
            },
            {
                "first_name": "Maria",
                "last_name": "Garcia",
                "date_of_birth": "1995-07-10",
                "insurance_provider": "State Medicaid",
                "insurance_type": "Medicaid",
                "email": "maria.garcia@email.com",
                "phone": "555-0106"
            },
            {
                "first_name": "David",
                "last_name": "Martinez",
                "date_of_birth": "1982-02-28",
                "insurance_provider": "Self-Pay",
                "insurance_type": "Self-pay",
                "email": "david.martinez@email.com",
                "phone": "555-0107"
            },
        ]

        created_patients = []
        for patient_data in patients_data:
            # Check if patient already exists by email
            existing_by_email = patient.get_patient(db, patient_id=1) if created_patients else None
            
            created_patient = patient.create_patient(db, PatientCreate(**patient_data))
            created_patients.append(created_patient)
            print(f"   ✅ Created patient: {created_patient.first_name} {created_patient.last_name} ({created_patient.insurance_type})")

        # ==================== BILLING RECORDS ====================
        print("\n[4/4] Creating Billing Records...")
        billing_data = [
            # John Doe - Private Insurance
            {
                "patient_id": created_patients[0].id,
                "procedure_id": created_procedures[0].id,  # Office visit
                "amount": 150.00,
                "status": "paid",
                "diagnosis_code": "J06.9"  # Upper respiratory infection
            },
            {
                "patient_id": created_patients[0].id,
                "procedure_id": created_procedures[3].id,  # Metabolic panel
                "amount": 75.00,
                "status": "paid",
                "diagnosis_code": "E11.9"  # Type 2 diabetes
            },
            
            # Jane Smith - Private Insurance
            {
                "patient_id": created_patients[1].id,
                "procedure_id": created_procedures[1].id,  # Office visit 25min
                "amount": 200.00,
                "status": "pending",
                "diagnosis_code": "I10"  # Hypertension
            },
            {
                "patient_id": created_patients[1].id,
                "procedure_id": created_procedures[5].id,  # EKG
                "amount": 125.00,
                "status": "paid",
                "diagnosis_code": "I10"  # Hypertension
            },
            
            # Michael Johnson - Private Insurance
            {
                "patient_id": created_patients[2].id,
                "procedure_id": created_procedures[4].id,  # CBC
                "amount": 45.00,
                "status": "paid",
                "diagnosis_code": "R51"  # Headache
            },
            {
                "patient_id": created_patients[2].id,
                "procedure_id": created_procedures[6].id,  # CT Head
                "amount": 650.00,
                "status": "denied",
                "diagnosis_code": "R51"  # Headache (high cost denial)
            },
            
            # Emily Williams - Private Insurance
            {
                "patient_id": created_patients[3].id,
                "procedure_id": created_procedures[0].id,  # Office visit
                "amount": 150.00,
                "status": "pending",
                "diagnosis_code": "M79.3"  # Chronic pain
            },
            {
                "patient_id": created_patients[3].id,
                "procedure_id": created_procedures[8].id,  # Physical therapy
                "amount": 100.00,
                "status": "paid",
                "diagnosis_code": "M79.3"  # Chronic pain
            },
            
            # Robert Brown - Medicare
            {
                "patient_id": created_patients[4].id,
                "procedure_id": created_procedures[1].id,  # Office visit
                "amount": 200.00,
                "status": "paid",
                "diagnosis_code": "E78.5"  # Hyperlipidemia
            },
            {
                "patient_id": created_patients[4].id,
                "procedure_id": created_procedures[3].id,  # Metabolic panel
                "amount": 75.00,
                "status": "paid",
                "diagnosis_code": "E78.5"  # Hyperlipidemia
            },
            
            # Maria Garcia - Medicaid
            {
                "patient_id": created_patients[5].id,
                "procedure_id": created_procedures[0].id,  # Office visit
                "amount": 150.00,
                "status": "denied",  # Medicaid denial
                "diagnosis_code": "J02.9"  # Pharyngitis
            },
            {
                "patient_id": created_patients[5].id,
                "procedure_id": created_procedures[7].id,  # Chest X-ray
                "amount": 150.00,
                "status": "pending",
                "diagnosis_code": "J44.9"  # COPD
            },
            
            # David Martinez - Self-pay
            {
                "patient_id": created_patients[6].id,
                "procedure_id": created_procedures[0].id,  # Office visit
                "amount": 150.00,
                "status": "denied",  # Self-pay high denial
                "diagnosis_code": "Z00.00"  # General exam
            },
            {
                "patient_id": created_patients[6].id,
                "procedure_id": created_procedures[9].id,  # Injection
                "amount": 45.00,
                "status": "pending",
                "diagnosis_code": "M25.5"  # Joint pain
            },
        ]

        created_billing_records = []
        for bill_data in billing_data:
            created_bill = billing_record.create_billing_record(db, BillingRecordCreate(**bill_data))
            created_billing_records.append(created_bill)
            print(f"   ✅ Created billing record #{created_bill.id}: ${created_bill.amount:.2f} ({created_bill.status}) - {bill_data['diagnosis_code']}")

        # ==================== SUMMARY ====================
        print("\n" + "=" * 60)
        print("✅ Database Seeding Complete!")
        print("=" * 60)
        print(f"   Users:           {len(created_users)}")
        print(f"   Procedures:      {len(created_procedures)}")
        print(f"   Patients:        {len(created_patients)}")
        print(f"   Billing Records: {len(created_billing_records)}")
        
        # Calculate some stats
        paid_count = sum(1 for b in billing_data if b['status'] == 'paid')
        denied_count = sum(1 for b in billing_data if b['status'] == 'denied')
        pending_count = sum(1 for b in billing_data if b['status'] == 'pending')
        total_billed = sum(b['amount'] for b in billing_data)
        
        print(f"\n   Status Breakdown:")
        print(f"      Paid:    {paid_count}")
        print(f"      Denied:  {denied_count}")
        print(f"      Pending: {pending_count}")
        print(f"   Total Billed: ${total_billed:.2f}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during database seeding: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()