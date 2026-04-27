import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Clinical Queue", page_icon="🩺", layout="wide")


def headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str):
    try:
        response = requests.get(f"{API_URL}{path}", headers=headers(), timeout=20)
        return response.status_code, response.json() if response.content else {}
    except Exception as exc:
        return 0, {"detail": str(exc)}


st.title("Clinical Billing Queue")
st.caption("A physician-facing slice of the billing workflow.")

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

if billing_df.empty:
    st.info("No claims yet.")
    st.stop()

if not patients_df.empty:
    patients_df["patient_name"] = patients_df["first_name"] + " " + patients_df["last_name"]
    billing_df = billing_df.merge(
        patients_df[["id", "patient_name", "insurance_type"]],
        left_on="patient_id",
        right_on="id",
        how="left",
        suffixes=("", "_patient"),
    )

billing_df["date"] = pd.to_datetime(billing_df["date"])
pending = billing_df[billing_df["status"] == "pending"].sort_values("date", ascending=False)
denied = billing_df[billing_df["status"] == "denied"].sort_values("date", ascending=False)

c1, c2, c3 = st.columns(3)
c1.metric("Pending Claims", len(pending))
c2.metric("Denied Claims", len(denied))
c3.metric("Flagged Claims", int(billing_df["is_flagged"].fillna(False).sum()) if "is_flagged" in billing_df else 0)

left, right = st.columns(2)
with left:
    st.subheader("Pending Review")
    st.dataframe(
        pending[["patient_name", "diagnosis_code", "amount", "date"]].head(15),
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.subheader("Denied Follow-up")
    st.dataframe(
        denied[["patient_name", "diagnosis_code", "amount", "date"]].head(15),
        use_container_width=True,
        hide_index=True,
    )
