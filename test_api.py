import requests

API_URL = "http://localhost:8000"

print("1. Logging in...")
login_response = requests.post(
    f"{API_URL}/auth/login",
    json={"username": "admin", "password": "adminadmin"}
)
print("Login status:", login_response.status_code)
print("Login body:", login_response.json())
login_response.raise_for_status()

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Token: {token[:20]}...")

print("\n2. Checking ML service health...")
health_response = requests.get(f"{API_URL}/ml/health")
print("ML health status:", health_response.status_code)
print("ML health body:", health_response.json())

print("\n3. Getting model info...")
info_response = requests.get(f"{API_URL}/ml/model/info", headers=headers)
print("Model info status:", info_response.status_code)
print("Model info text:", info_response.text)
info_response.raise_for_status()
print("Model info body:", info_response.json())

print("\n4. Making a prediction...")
prediction_input = {
    "patient_age": 65,
    "insurance_type": "Medicare",
    "procedure_cpt_code": "99214",
    "diagnosis_code": "E11.9",
    "billed_amount": 250.00,
    "days_since_last_claim": 45,
    "num_prior_claims": 3,
    "prior_denial_rate": 0.33
}

pred_response = requests.post(
    f"{API_URL}/ml/predict/denial",
    json=prediction_input,
    headers=headers
)
print("Prediction status:", pred_response.status_code)
print("Prediction text:", pred_response.text)
pred_response.raise_for_status()
result = pred_response.json()
print(f"Risk Level: {result['risk_level']}")
print(f"Denial Probability: {result['denial_probability']:.1%}")