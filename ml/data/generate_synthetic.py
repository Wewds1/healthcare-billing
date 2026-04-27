import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

CPT_CODES = [
    "99213", "99214", "99215",
    "99281", "99282", "99283", "99284", "99285",
    "36415", "80053", "85025", "93000", "70450", "71020",
    "73610", "80061", "82947", "87070", "96372", "97110",
]

ICD10_CODES = [
    "J06.9", "E11.9", "I10", "M79.3", "R51",
    "J44.9", "K21.9", "E78.5", "M25.5", "R10.9",
    "F41.9", "S93.4", "J02.9", "N39.0", "Z00.00",
]

INSURANCE_TYPES = ["Medicare", "Medicaid", "Private", "Self-pay"]

PROCEDURE_SITE_OF_SERVICE = {
    "99213": "Office", "99214": "Office", "99215": "Office",
    "99281": "Emergency", "99282": "Emergency", "99283": "Emergency", "99284": "Emergency", "99285": "Emergency",
    "36415": "Office", "80053": "Outpatient", "85025": "Outpatient",
    "93000": "Office", "70450": "Imaging Center", "71020": "Imaging Center",
    "73610": "Imaging Center", "80061": "Outpatient", "82947": "Outpatient",
    "87070": "Outpatient", "96372": "Office", "97110": "Outpatient",
}

CPT_PRICE_RANGES = {
    "99213": (100, 150), "99214": (150, 200), "99215": (200, 300),
    "99281": (150, 250), "99282": (250, 400), "99283": (400, 600),
    "99284": (600, 900), "99285": (900, 1500),
    "36415": (20, 40), "80053": (80, 120), "85025": (40, 70),
    "93000": (50, 100), "70450": (500, 800), "71020": (100, 200),
    "73610": (100, 180), "80061": (60, 100), "82947": (20, 40),
    "87070": (80, 150), "96372": (30, 60), "97110": (80, 150),
}

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


def generate_patient_claims(num_records=120000):
    records = []
    next_patient_id = 1
    patient_history = {}
    high_cost_cpts = {"99284", "99285", "70450"}

    for _ in range(num_records):
        if random.random() < 0.75 and patient_history:
            patient_id = random.choice(list(patient_history.keys()))
        else:
            patient_id = next_patient_id
            next_patient_id += 1
            patient_history[patient_id] = {
                "age": random.randint(18, 90),
                "insurance": random.choice(INSURANCE_TYPES),
                "claims": [],
                "denial_count": 0,
            }

        patient = patient_history[patient_id]
        diagnosis_code = random.choice(ICD10_CODES)

        if random.random() < 0.86:
            procedure_cpt = random.choice(VALID_PAIRS.get(diagnosis_code, CPT_CODES[:5]))
        else:
            procedure_cpt = random.choice(CPT_CODES)

        price_range = CPT_PRICE_RANGES.get(procedure_cpt, (50, 200))
        billed_amount = round(random.uniform(*price_range) * random.uniform(0.90, 1.10), 2)
        place_of_service = PROCEDURE_SITE_OF_SERVICE.get(procedure_cpt, "Office")
        claim_type = "Institutional" if place_of_service in {"Emergency", "Imaging Center"} and random.random() < 0.4 else "Professional"

        if patient["insurance"] == "Self-pay":
            network_status = "Out of Network"
        elif patient["insurance"] == "Private":
            network_status = "Out of Network" if random.random() < 0.18 else "In Network"
        else:
            network_status = "Out of Network" if random.random() < 0.08 else "In Network"

        units = random.randint(1, 6) if procedure_cpt in {"97110", "96372"} else 1
        authorization_required = int(procedure_cpt in {"70450", "99284", "99285", "97110"} or billed_amount > 600)
        authorization_on_file = 1 if authorization_required == 0 else int(random.random() < 0.83)

        if patient["claims"]:
            last_claim_date = patient["claims"][-1]["date"]
            current_date = last_claim_date + timedelta(days=random.randint(1, 180))
            days_since_last_claim = (current_date - last_claim_date).days
        else:
            current_date = datetime.now() - timedelta(days=random.randint(0, 365))
            days_since_last_claim = 999

        num_prior_claims = len(patient["claims"])
        prior_denial_rate = patient["denial_count"] / max(num_prior_claims, 1)

        is_code_mismatch = 1 if procedure_cpt not in VALID_PAIRS.get(diagnosis_code, []) else 0
        is_high_cost_procedure = 1 if procedure_cpt in high_cost_cpts else 0
        is_frequent_claimer = 1 if (num_prior_claims > 3 and days_since_last_claim < 30) else 0
        is_recent_repeat_claim = 1 if days_since_last_claim < 7 else 0

        denial_prob = 0.10

        if patient["insurance"] == "Self-pay":
            denial_prob += 0.30
        elif patient["insurance"] == "Medicaid":
            denial_prob += 0.10
        elif patient["insurance"] == "Medicare":
            denial_prob += 0.05

        if patient["insurance"] == "Medicaid" and is_high_cost_procedure:
            denial_prob += 0.20
        if network_status == "Out of Network":
            denial_prob += 0.16
        if authorization_required and not authorization_on_file:
            denial_prob += 0.32
        if claim_type == "Institutional" and patient["insurance"] in {"Self-pay", "Medicaid"}:
            denial_prob += 0.08
        if place_of_service == "Emergency" and patient["insurance"] != "Self-pay":
            denial_prob -= 0.03
        if units >= 4:
            denial_prob += 0.08
        if is_code_mismatch:
            denial_prob += 0.35
        if is_frequent_claimer:
            denial_prob += 0.25
        if prior_denial_rate > 0.5:
            denial_prob += 0.25
        elif prior_denial_rate > 0.3:
            denial_prob += 0.12

        pct_in_range = (billed_amount - price_range[0]) / max(price_range[1] - price_range[0], 1)
        denial_prob += max(0.0, pct_in_range) * 0.08

        if random.random() < 0.04:
            denial_prob += random.uniform(-0.20, 0.20)

        denial_prob = float(np.clip(denial_prob, 0.01, 0.95))
        claim_status = 1 if random.random() < denial_prob else 0

        anomaly_label = 0
        median_price = sum(price_range) / 2.0
        if billed_amount > median_price * 3:
            anomaly_label = 1
        if is_recent_repeat_claim:
            anomaly_label = 1
        if billed_amount == 0 or billed_amount > 50000:
            anomaly_label = 1
        if num_prior_claims > 10 and days_since_last_claim < 14:
            anomaly_label = 1
        if random.random() < 0.08 and anomaly_label == 0:
            anomaly_label = 1

        records.append(
            {
                "patient_id": patient_id,
                "patient_age": patient["age"],
                "insurance_type": patient["insurance"],
                "procedure_cpt_code": procedure_cpt,
                "diagnosis_code": diagnosis_code,
                "billed_amount": billed_amount,
                "days_since_last_claim": days_since_last_claim,
                "num_prior_claims": num_prior_claims,
                "prior_denial_rate": round(prior_denial_rate, 3),
                "place_of_service": place_of_service,
                "claim_type": claim_type,
                "network_status": network_status,
                "authorization_required": authorization_required,
                "authorization_on_file": authorization_on_file,
                "units": units,
                "is_code_mismatch": is_code_mismatch,
                "is_high_cost_procedure": is_high_cost_procedure,
                "is_frequent_claimer": is_frequent_claimer,
                "is_recent_repeat_claim": is_recent_repeat_claim,
                "claim_status": claim_status,
                "anomaly_label": anomaly_label,
                "date": current_date.strftime("%Y-%m-%d"),
            }
        )

        patient["claims"].append({"date": current_date})
        if claim_status == 1:
            patient["denial_count"] += 1

    return pd.DataFrame(records)


def main():
    print("Generating synthetic patient claims data...")
    df = generate_patient_claims(num_records=120000)
    output_path = "ml/data/synthetic_billing.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    print(f"Rows: {len(df)} | Denial rate: {df['claim_status'].mean():.2%}")


if __name__ == "__main__":
    main()
