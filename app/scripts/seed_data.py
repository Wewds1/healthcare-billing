import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.crud import billing_record, patient, procedure, user
from app.database import SessionLocal
from app.schemas.billing_record import BillingRecordCreate
from app.schemas.patient import PatientCreate
from app.schemas.procedure import ProcedureCreate
from app.schemas.user import UserCreate

RNG = random.Random(42)

PROCEDURES = [
    {"cpt_code": "99213", "description": "Office Visit - Established Patient (15 min)", "price": 145},
    {"cpt_code": "99214", "description": "Office Visit - Established Patient (25 min)", "price": 195},
    {"cpt_code": "99215", "description": "Office Visit - Established Patient (40 min)", "price": 295},
    {"cpt_code": "99282", "description": "Emergency Department Visit - Low Severity", "price": 285},
    {"cpt_code": "99283", "description": "Emergency Department Visit - Moderate Severity", "price": 465},
    {"cpt_code": "36415", "description": "Venipuncture", "price": 28},
    {"cpt_code": "80053", "description": "Comprehensive Metabolic Panel", "price": 84},
    {"cpt_code": "80061", "description": "Lipid Panel", "price": 78},
    {"cpt_code": "82947", "description": "Glucose Test", "price": 32},
    {"cpt_code": "85025", "description": "Complete Blood Count", "price": 49},
    {"cpt_code": "87070", "description": "Culture, Bacterial", "price": 112},
    {"cpt_code": "93000", "description": "Electrocardiogram", "price": 118},
    {"cpt_code": "70450", "description": "CT Head without Contrast", "price": 645},
    {"cpt_code": "71020", "description": "Chest X-ray", "price": 158},
    {"cpt_code": "73610", "description": "Ankle X-ray", "price": 141},
    {"cpt_code": "96372", "description": "Therapeutic Injection", "price": 52},
    {"cpt_code": "97110", "description": "Physical Therapy - Therapeutic Exercise", "price": 108},
    {"cpt_code": "97140", "description": "Manual Therapy", "price": 96},
]

PATIENT_TEMPLATES = [
    ("John", "Doe", "1980-05-15", "Blue Cross Blue Shield", "Private"),
    ("Jane", "Smith", "1992-08-22", "Aetna", "Private"),
    ("Michael", "Johnson", "1975-12-03", "UnitedHealthcare", "Private"),
    ("Emily", "Williams", "1988-03-17", "Cigna", "Private"),
    ("Robert", "Brown", "1965-11-28", "Medicare Part A", "Medicare"),
    ("Maria", "Garcia", "1995-07-10", "State Medicaid", "Medicaid"),
    ("David", "Martinez", "1982-02-28", "Self-Pay", "Self-pay"),
    ("Sophia", "Anderson", "1971-01-19", "Humana Medicare Advantage", "Medicare"),
    ("James", "Taylor", "1986-09-09", "Kaiser Permanente", "Private"),
    ("Olivia", "Thomas", "1998-04-01", "State Medicaid", "Medicaid"),
    ("Daniel", "Moore", "1960-06-12", "Medicare Part B", "Medicare"),
    ("Ava", "Jackson", "1990-12-14", "Blue Shield PPO", "Private"),
]

DIAGNOSIS_TO_CPTS = {
    "J06.9": ["99213", "99214", "36415", "87070"],
    "E11.9": ["99213", "99214", "82947", "80053"],
    "I10": ["99213", "99214", "93000", "80053"],
    "M79.3": ["99213", "99214", "97110", "97140", "96372"],
    "R51": ["99213", "99214", "70450"],
    "J44.9": ["99214", "99215", "71020", "93000"],
    "E78.5": ["99213", "80061"],
    "M25.5": ["99213", "73610", "97110", "97140"],
    "J02.9": ["99213", "87070"],
    "Z00.00": ["99213", "99214", "85025", "80053"],
}

INSURANCE_STATUS_WEIGHTS = {
    "Private": ["paid", "paid", "paid", "pending", "denied"],
    "Medicare": ["paid", "paid", "pending", "paid", "denied"],
    "Medicaid": ["paid", "pending", "pending", "denied", "denied"],
    "Self-pay": ["pending", "denied", "denied", "paid", "pending"],
}


def ensure_users(db):
    payloads = [
        {"username": "admin", "email": "admin@hospital.com", "role": "admin", "password": "adminadmin"},
        {"username": "doctor1", "email": "doctor1@hospital.com", "role": "user", "password": "Doctor123!"},
        {"username": "billing_staff", "email": "billing@hospital.com", "role": "user", "password": "Staff123!"},
    ]

    created = []
    for payload in payloads:
        existing = user.get_user_by_username(db, payload["username"])
        if existing:
            created.append(existing)
            print(f"   user exists: {existing.username}")
            continue
        created.append(user.create_user(db, UserCreate(**payload)))
        print(f"   created user: {payload['username']}")
    return created


def ensure_procedures(db):
    created = []
    for payload in PROCEDURES:
        existing = procedure.get_procedure_by_cpt_code(db, payload["cpt_code"])
        if existing:
            created.append(existing)
            continue
        created.append(procedure.create_procedure(db, ProcedureCreate(**payload)))
    print(f"   procedures available: {len(created)}")
    return {item.cpt_code: item for item in created}


def ensure_patients(db):
    created = []
    for index, (first_name, last_name, dob, provider, insurance_type) in enumerate(PATIENT_TEMPLATES, start=1):
        email = f"{first_name.lower()}.{last_name.lower()}@examplehealth.org"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
            "insurance_provider": provider,
            "insurance_type": insurance_type,
            "email": email,
            "phone": f"555-01{index:02d}",
        }
        existing = patient.get_patient_by_email(db, email=email)
        if existing:
            created.append(existing)
            continue
        created.append(patient.create_patient(db, PatientCreate(**payload)))
    print(f"   patients available: {len(created)}")
    return created


def build_billing_payloads(patients, procedures_by_cpt):
    diagnosis_codes = list(DIAGNOSIS_TO_CPTS.keys())
    records = []

    for patient_row in patients:
        preferred_statuses = INSURANCE_STATUS_WEIGHTS.get(patient_row.insurance_type, ["paid", "pending", "denied"])
        claim_count = 6 if patient_row.insurance_type in {"Medicaid", "Self-pay"} else 5

        for _ in range(claim_count):
            diagnosis_code = RNG.choice(diagnosis_codes)
            cpt_code = RNG.choice(DIAGNOSIS_TO_CPTS[diagnosis_code])
            procedure_row = procedures_by_cpt[cpt_code]
            amount = round(procedure_row.price * RNG.uniform(0.95, 1.18), 2)
            status = RNG.choice(preferred_statuses)

            if patient_row.insurance_type == "Self-pay" and amount > 250:
                status = RNG.choice(["pending", "denied", "denied"])
            elif patient_row.insurance_type == "Medicare" and cpt_code in {"99213", "80053", "80061"}:
                status = RNG.choice(["paid", "paid", "pending"])

            records.append(
                BillingRecordCreate(
                    patient_id=patient_row.id,
                    procedure_id=procedure_row.id,
                    amount=amount,
                    status=status,
                    diagnosis_code=diagnosis_code,
                )
            )

    return records


def ensure_billing_records(db, patients, procedures_by_cpt):
    existing = billing_record.get_billing_records(db, skip=0, limit=1)
    if existing:
        total_existing = len(billing_record.get_billing_records(db, skip=0, limit=10000))
        print(f"   billing records already present: {total_existing}")
        return total_existing

    payloads = build_billing_payloads(patients, procedures_by_cpt)
    for payload in payloads:
        billing_record.create_billing_record(db, payload)
    print(f"   created billing records: {len(payloads)}")
    return len(payloads)


def seed_database():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("Starting database seeding")
        print("=" * 60)

        print("\n[1/4] Users")
        created_users = ensure_users(db)

        print("\n[2/4] Procedures")
        procedures_by_cpt = ensure_procedures(db)

        print("\n[3/4] Patients")
        created_patients = ensure_patients(db)

        print("\n[4/4] Billing records")
        billing_count = ensure_billing_records(db, created_patients, procedures_by_cpt)

        print("\n" + "=" * 60)
        print("Database seeding complete")
        print("=" * 60)
        print(f"   users: {len(created_users)}")
        print(f"   procedures: {len(procedures_by_cpt)}")
        print(f"   patients: {len(created_patients)}")
        print(f"   billing records: {billing_count}")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
