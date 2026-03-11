import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

CPT_CODES = [
    "99213", "99214", "99215",  # Office visits
    "99281", "99282", "99283", "99284", "99285",  # Emergency visits
    "36415",  # Venipuncture
    "80053",  # Comprehensive metabolic panel
    "85025",  # Complete blood count
    "93000",  # EKG
    "70450",  # CT head without contrast
    "71020",  # Chest X-ray
    "73610",  # Ankle X-ray
    "80061",  # Lipid panel
    "82947",  # Glucose test
    "87070",  # Culture, bacterial
    "96372",  # Injection
    "97110",  # Physical therapy
]

ICD10_CODES = [
    "J06.9",   # Upper respiratory infection
    "E11.9",   # Type 2 diabetes
    "I10",     # Essential hypertension
    "M79.3",   # Chronic pain
    "R51",     # Headache
    "J44.9",   # COPD
    "K21.9",   # GERD
    "E78.5",   # Hyperlipidemia
    "M25.5",   # Joint pain
    "R10.9",   # Abdominal pain
    "F41.9",   # Anxiety disorder
    "S93.4",   # Sprain of ankle
    "J02.9",   # Acute pharyngitis
    "N39.0",   # UTI
    "Z00.00",  # General exam
]

INSURANCE_TYPES = ["Medicare", "Medicaid", "Private", "Self-pay"]

# Realistic price ranges per CPT code
CPT_PRICE_RANGES = {
    "99213": (100, 150), "99214": (150, 200), "99215": (200, 300),
    "99281": (150, 250), "99282": (250, 400), "99283": (400, 600),
    "99284": (600, 900), "99285": (900, 1500),
    "36415": (20, 40), "80053": (80, 120), "85025": (40, 70),
    "93000": (50, 100), "70450": (500, 800), "71020": (100, 200),
    "73610": (100, 180), "80061": (60, 100), "82947": (20, 40),
    "87070": (80, 150), "96372": (30, 60), "97110": (80, 150),
}

# Diagnosis-Procedure compatibility matrix (realistic pairings)
VALID_PAIRS = {
    "J06.9": ["99213", "99214", "36415", "87070"],
    "E11.9": ["99213", "99214", "82947", "80053"],
    "I10": ["99213", "99214", "93000", "80053"],
    "M79.3": ["99213", "99214", "97110", "96372"],
    "R51": ["99213", "99214", "70450"],
    "J44.9": ["99214", "99215", "71020", "93000"],
    "K21.9": ["99213", "80053"],
    "E78.5": ["99213", "80061"],
    "M25.5": ["99213", "73610", "97110"],
    "R10.9": ["99213", "99214", "80053"],
    "F41.9": ["99213", "99214"],
    "S93.4": ["99282", "99283", "73610", "96372"],
    "J02.9": ["99213", "87070"],
    "N39.0": ["99213", "87070", "80053"],
    "Z00.00": ["99213", "99214", "85025", "80053"],
}


def generate_patient_claims(num_records=5000):
    records = []
    num_patients = num_records // 3

    patient_history = {}

    for record_id in range(num_records):
        if random.random() < 0.7 and patient_history:
            patient_id = random.choice(list(patient_history.keys()))
        else:
            patient_id = random.randint(1, num_patients)
            patient_history[patient_id] = {
                "age": random.randint(0, 100),
                "insurance": random.choice(INSURANCE_TYPES),
                "claims": [],
                "denial_count": 0
            }
        patient = patient_history[patient_id]


        diagnosis_code = random.choice(ICD10_CODES)


        if random.random() < 0.8:
            procedure_cpt = random.choice(VALID_PAIRS.get(diagnosis_code, CPT_CODES[:5]))
        else:
            procedure_cpt = random.choice(CPT_CODES)


        price_range = CPT_PRICE_RANGES.get(procedure_cpt, (50, 200))
        base_amount = random.uniform(*price_range)
        billed_amount = round(base_amount * random.uniform(0.9, 1.1), 2)

        days_since_last_claim = 999
        if patient['claims']:
            last_claim_date = patient['claims'][-1]['date']
            current_date = last_claim_date + timedelta(days=random.randint(1, 180))
            days_since_last_claim = (current_date - last_claim_date).days
        else:
            current_date = datetime.now() - timedelta(days=random.randint(0, 365))


        num_prior_claims = len(patient['claims'])
        prior_denial_rate = patient["denial_count"] / max(num_prior_claims, 1)
        denial_prob = 0.15

        if patient['insurance'] == "Self-pay":
            denial_prob += 0.25
        elif patient['insurance'] == "Medicaid":
            denial_prob += 0.1
        elif patient['insurance'] == "Medicare":
            denial_prob += 0.05

        if billed_amount > 500:
            denial_prob += 0.1

        if num_prior_claims > 3 and days_since_last_claim < 30:
            denial_prob += 0.15

        if procedure_cpt not in VALID_PAIRS.get(diagnosis_code, []):
            denial_prob += 0.25

        if prior_denial_rate > 0.5:
            denial_prob += 0.2
        
        if random.random() < 0.12:
            denial_prob = random.uniform(0, 1)

        claim_status = 1 if random.random() < denial_prob else 0

        anomaly_label = 0


        median_price = sum(price_range) / 2
        if billed_amount > median_price * 3:
            anomaly_label = 1
        
        if days_since_last_claim < 7:
            anomaly_label = 1
        
        if billed_amount == 0 or billed_amount > 50000:
            anomaly_label = 1
        
        if num_prior_claims > 10 and days_since_last_claim < 14:
            anomaly_label = 1
        
        if random.random() < 0.08 and anomaly_label == 0:
            anomaly_label = 1
        

        record = {
            "patient_id": patient_id,
            "patient_age": patient["age"],
            "insurance_type": patient["insurance"],
            "procedure_cpt_code": procedure_cpt,
            "diagnosis_code": diagnosis_code,
            "billed_amount": billed_amount,
            "days_since_last_claim": days_since_last_claim,
            "num_prior_claims": num_prior_claims,
            "prior_denial_rate": round(prior_denial_rate, 3),
            "claim_status": claim_status,
            "anomaly_label": anomaly_label,
            "date": current_date.strftime("%Y-%m-%d"),
        }

        records.append(record)
        
        patient["claims"].append({"date": current_date})
        if claim_status == 1:
            patient["denial_count"] += 1
    
    return pd.DataFrame(records)



def main():
    print("Generating synthetic patient claims data...")

    df = generate_patient_claims(num_records=5000)

    output_path = "ml/data/synthetic_billing.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()