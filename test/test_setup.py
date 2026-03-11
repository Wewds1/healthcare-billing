"""
Quick test script to verify DAY 1 setup
Run: python test_setup.py
"""
import requests
import pandas as pd
from pathlib import Path

API_URL = "http://localhost:8000"

def test_api_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("   [PASS] API is running")
            return True
        else:
            print(f"   [FAIL] API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   [FAIL] Cannot connect to API: {e}")
        return False

def test_auth():
    """Test JWT authentication"""
    try:
        # FIX: Correct password is "adminadmin"
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": "admin", "password": "adminadmin"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   [PASS] Authentication works - Token received")
            return token
        else:
            print(f"   [FAIL] Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   [FAIL] Auth test failed: {e}")
        return None

def test_protected_endpoint(token):
    """Test RBAC protection"""
    # FIX: Correct header is "Authorization" not "Authentication"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with token
    response = requests.get(f"{API_URL}/users/", headers=headers)
    if response.status_code == 200:
        print(f"   [PASS] RBAC works - Protected endpoint accessible with token")
    else:
        print(f"   [FAIL] Protected endpoint failed: {response.status_code}")
    
    # Test without token
    response = requests.get(f"{API_URL}/users/")
    if response.status_code == 401 or response.status_code == 403:
        print(f"   [PASS] RBAC works - Protected endpoint blocked without token")
    else:
        print(f"   [WARN] Protected endpoint returned {response.status_code}, expected 401/403")

def test_synthetic_data():
    """Verify synthetic data file"""
    csv_path = Path("ml/data/synthetic_billing.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"   [PASS] Synthetic data exists: {len(df)} records")
        print(f"          Columns: {list(df.columns)}")
        print(f"          Denial rate: {df['claim_status'].mean():.2%}")
        print(f"          Anomaly rate: {df['anomaly_label'].mean():.2%}")
        return True
    else:
        print(f"   [FAIL] Synthetic data not found at {csv_path}")
        return False

def test_database_fields():
    """Test new database fields"""
    token = test_auth()
    if not token:
        return
    
    # FIX: Correct header is "Authorization" not "Authentication"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check patients have new fields
    response = requests.get(f"{API_URL}/patients/", headers=headers)
    if response.status_code == 200:
        patients = response.json()
        if patients:
            # FIX: Was "patient = patient[0]", should be "patients[0]"
            patient = patients[0]
            has_insurance_type = "insurance_type" in patient
            has_email = "email" in patient
            has_phone = "phone" in patient
            
            if has_insurance_type and has_email and has_phone:
                print(f"   [PASS] Patient model has all new fields")
                print(f"          insurance_type={patient.get('insurance_type')}, email={patient.get('email')}, phone={patient.get('phone')}")
            else:
                print(f"   [FAIL] Patient missing fields: insurance_type={has_insurance_type}, email={has_email}, phone={has_phone}")
        else:
            print(f"   [WARN] No patients in database. Run seed script first.")
    else:
        print(f"   [FAIL] Could not fetch patients: {response.status_code}")
    
    # Check billing records have new fields
    response = requests.get(f"{API_URL}/billing/", headers=headers)
    if response.status_code == 200:
        records = response.json()
        if records:
            record = records[0]
            has_diagnosis = "diagnosis_code" in record
            has_anomaly = "anomaly_score" in record
            has_flagged = "is_flagged" in record
            
            if has_diagnosis and has_anomaly and has_flagged:
                print(f"   [PASS] BillingRecord model has all new fields")
                print(f"          diagnosis_code={record.get('diagnosis_code')}, anomaly_score={record.get('anomaly_score')}, is_flagged={record.get('is_flagged')}")
            else:
                print(f"   [FAIL] BillingRecord missing fields: diagnosis_code={has_diagnosis}, anomaly_score={has_anomaly}, is_flagged={has_flagged}")
        else:
            print(f"   [WARN] No billing records in database. Run seed script first.")
    else:
        print(f"   [FAIL] Could not fetch billing records: {response.status_code}")

def main():
    print("=" * 60)
    print("DAY 1 Setup Verification")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n[1] Testing API Health...")
    if not test_api_health():
        print("\n   [ACTION] API not running. Start with: docker compose up -d")
        return
    
    # Test 2: Authentication
    print("\n[2] Testing Authentication & RBAC...")
    token = test_auth()
    if token:
        test_protected_endpoint(token)
    
    # Test 3: Synthetic Data
    print("\n[3] Checking Synthetic Data...")
    test_synthetic_data()
    
    # Test 4: Database Fields
    print("\n[4] Verifying New Database Fields...")
    test_database_fields()
    
    print("\n" + "=" * 60)
    print("DAY 1 Verification Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()