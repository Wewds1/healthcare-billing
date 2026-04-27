import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Patients", page_icon="👥", layout="wide")


def headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str):
    try:
        response = requests.get(f"{API_URL}{path}", headers=headers(), timeout=20)
        return response.status_code, response.json() if response.content else {}
    except Exception as exc:
        return 0, {"detail": str(exc)}


st.title("Patient Ledger View")
st.caption("Searchable patient list with claim totals.")

if not st.session_state.get("token"):
    st.warning("Sign in from the main dashboard first.")
    st.stop()

patient_status, patients = api_get("/patients/")
billing_status, billing_records = api_get("/billing/")

if 0 in {patient_status, billing_status}:
    st.error("API unavailable.")
    st.stop()

patients_df = pd.DataFrame(patients)
billing_df = pd.DataFrame(billing_records)

if patients_df.empty:
    st.info("No patients available.")
    st.stop()

patients_df["patient_name"] = patients_df["first_name"] + " " + patients_df["last_name"]

if not billing_df.empty:
    balances = billing_df.groupby("patient_id", as_index=False)["amount"].sum().rename(columns={"amount": "total_billed"})
    patients_df = patients_df.merge(balances, left_on="id", right_on="patient_id", how="left")
    patients_df["total_billed"] = patients_df["total_billed"].fillna(0.0)
else:
    patients_df["total_billed"] = 0.0

search = st.text_input("Search patient")
directory = patients_df.copy()
if search:
    mask = directory.astype(str).apply(lambda column: column.str.contains(search, case=False, na=False))
    directory = directory[mask.any(axis=1)]

st.dataframe(
    directory[["patient_name", "insurance_type", "insurance_provider", "email", "phone", "total_billed"]],
    use_container_width=True,
    hide_index=True,
)
