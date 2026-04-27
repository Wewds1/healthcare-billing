import os
from typing import Dict, List

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Helix Billing Command Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def inject_theme():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f5f7fb;
            --panel: #ffffff;
            --ink: #0f172a;
            --muted: #475569;
            --line: #dbe3ef;
            --brand: #0f766e;
            --brand-soft: #ccfbf1;
            --accent: #b45309;
            --accent-soft: #ffedd5;
            --danger: #b91c1c;
            --danger-soft: #fee2e2;
        }
        .stApp {
            background: linear-gradient(180deg, #eef4ff 0%, #f7fafc 22%, #f5f7fb 100%);
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }
        .hero {
            background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(15,23,42,0.06));
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .hero h1, .hero h3, .hero p {
            margin: 0;
        }
        .hero h1 {
            color: var(--ink);
            font-size: 2rem;
            font-weight: 700;
        }
        .hero p {
            color: var(--muted);
            margin-top: 0.55rem;
        }
        .stat-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1rem 0.9rem 1rem;
            min-height: 112px;
        }
        .stat-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0;
        }
        .stat-value {
            color: var(--ink);
            font-size: 1.85rem;
            font-weight: 700;
            margin-top: 0.35rem;
        }
        .stat-subtle {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 0.3rem;
        }
        .panel-title {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }
        .status-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 0.18rem 0.6rem;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .pill-good {
            background: var(--brand-soft);
            color: var(--brand);
        }
        .pill-warn {
            background: var(--accent-soft);
            color: var(--accent);
        }
        .pill-risk {
            background: var(--danger-soft);
            color: var(--danger);
        }
        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid #1e293b;
        }
        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.7);
            padding: 0 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            background: #ffffff !important;
            border-color: #94a3b8 !important;
        }
        .stDataFrame, .stTable {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def api_get(path: str):
    try:
        response = requests.get(f"{API_URL}{path}", headers=get_headers(), timeout=20)
        return response.status_code, response.json() if response.content else {}
    except Exception as exc:
        return 0, {"detail": str(exc)}


def api_post(path: str, payload: Dict):
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, headers=get_headers(), timeout=20)
        body = response.json() if response.content else {}
        return response.status_code, body
    except Exception as exc:
        return 0, {"detail": str(exc)}


def login(username: str, password: str) -> bool:
    status_code, body = api_post("/auth/login", {"username": username, "password": password})
    if status_code == 200:
        st.session_state.token = body["access_token"]
        st.session_state.user = body["user"]
        return True
    st.error(body.get("detail", "Login failed"))
    return False


def logout():
    st.session_state.token = None
    st.session_state.user = None


def metric_card(label: str, value: str, subtle: str = ""):
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-subtle">{subtle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(value: str) -> str:
    lowered = value.lower()
    if lowered == "paid":
        return '<span class="status-pill pill-good">Paid</span>'
    if lowered == "pending":
        return '<span class="status-pill pill-warn">Pending</span>'
    return '<span class="status-pill pill-risk">Denied</span>'


def build_joined_frames(patients: List[Dict], procedures: List[Dict], billing_records: List[Dict]):
    patients_df = pd.DataFrame(patients)
    procedures_df = pd.DataFrame(procedures)
    billing_df = pd.DataFrame(billing_records)

    if billing_df.empty:
        return patients_df, procedures_df, billing_df

    if not patients_df.empty:
        patients_df["patient_name"] = patients_df["first_name"] + " " + patients_df["last_name"]
        billing_df = billing_df.merge(
            patients_df[["id", "patient_name", "insurance_type"]],
            left_on="patient_id",
            right_on="id",
            how="left",
            suffixes=("", "_patient"),
        )
        billing_df = billing_df.drop(columns=["id_patient"], errors="ignore")

    if not procedures_df.empty:
        billing_df = billing_df.merge(
            procedures_df[["id", "cpt_code", "description", "price"]],
            left_on="procedure_id",
            right_on="id",
            how="left",
            suffixes=("", "_procedure"),
        )
        billing_df = billing_df.drop(columns=["id_procedure"], errors="ignore")

    billing_df["date"] = pd.to_datetime(billing_df["date"])
    return patients_df, procedures_df, billing_df


def render_marketing_shell():
    st.markdown(
        """
        <div class="hero">
            <h1>Helix Billing Command Center</h1>
            <p>Revenue-cycle operations, denial risk review, OCR intake, and patient billing activity in one streamlined demo surface.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Demo Dataset", "120K", "Synthetic claims ready for model training")
    with c2:
        metric_card("Workflows", "4", "Claims, patient intake, billing, risk scoring")
    with c3:
        metric_card("Stack", "FastAPI + ML", "API, Streamlit, OCR, classical ML")

    st.markdown("")
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("### Sign in")
        with st.form("login_form"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="adminadmin")
            submitted = st.form_submit_button("Access Workspace", use_container_width=True)
            if submitted and login(username, password):
                st.rerun()
    with right:
        st.markdown("### Snapshot")
        st.markdown(
            """
            - Operational dashboard with joined patient, procedure, and claim views
            - Denial prediction endpoint with interpretable feature ranking
            - OCR intake hooks for document-driven claim creation
            - Demo-safe local database fallback for quick portfolio runs
            """
        )


def render_sidebar():
    with st.sidebar:
        st.markdown("## Helix Billing")
        st.caption("Healthcare revenue operations demo")

        health_code, health = api_get("/health")
        if health_code == 200:
            health_status = health.get("status", "unknown").title()
            st.write(f"Platform: {health_status}")
            st.write(f"Database: {health.get('database', 'unknown')}")
        else:
            st.write("Platform: unavailable")

        st.markdown("---")
        st.write(f"User: `{st.session_state.user['username']}`")
        st.write(f"Role: `{st.session_state.user['role']}`")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()


def render_dashboard():
    patient_code, patients = api_get("/patients/")
    procedure_code, procedures = api_get("/procedures/")
    billing_code, billing_records = api_get("/billing/")

    if 0 in {patient_code, procedure_code, billing_code}:
        st.error("The API is not reachable from the dashboard.")
        return

    patients_df, procedures_df, billing_df = build_joined_frames(patients, procedures, billing_records)

    st.markdown(
        """
        <div class="hero">
            <h1>Revenue Operations Workspace</h1>
            <p>Operational claims visibility with denial pressure, patient mix, and billing activity surfaced for a portfolio-friendly demo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_revenue = billing_df["amount"].sum() if not billing_df.empty else 0
    paid_rate = (
        (billing_df["status"].eq("paid").sum() / len(billing_df)) * 100 if not billing_df.empty else 0
    )
    flagged_count = int(billing_df["is_flagged"].fillna(False).sum()) if "is_flagged" in billing_df else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Net Charges", f"${total_revenue:,.0f}", f"{len(billing_df)} total claims")
    with m2:
        metric_card("Patients", f"{len(patients_df):,}", "Active directory records")
    with m3:
        metric_card("Paid Rate", f"{paid_rate:.1f}%", "Current paid claim share")
    with m4:
        metric_card("Flagged Claims", f"{flagged_count}", "Anomaly scan output")

    tabs = st.tabs(["Command Center", "Revenue Ops", "Patients", "Claim Intake"])

    with tabs[0]:
        col1, col2 = st.columns([1.3, 1])
        with col1:
            st.markdown('<div class="panel-title">Claims Timeline</div>', unsafe_allow_html=True)
            if not billing_df.empty:
                trend_df = (
                    billing_df.assign(day=billing_df["date"].dt.date)
                    .groupby(["day", "status"], as_index=False)["amount"]
                    .sum()
                )
                fig = px.area(
                    trend_df,
                    x="day",
                    y="amount",
                    color="status",
                    color_discrete_map={"paid": "#0f766e", "pending": "#d97706", "denied": "#b91c1c"},
                )
                fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No billing data yet.")

        with col2:
            st.markdown('<div class="panel-title">Payer Mix</div>', unsafe_allow_html=True)
            if not billing_df.empty and "insurance_type" in billing_df:
                payer_mix = billing_df.groupby("insurance_type", as_index=False)["amount"].sum()
                fig = px.pie(
                    payer_mix,
                    names="insurance_type",
                    values="amount",
                    color_discrete_sequence=["#0f766e", "#0ea5e9", "#d97706", "#b91c1c"],
                    hole=0.55,
                )
                fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No payer mix available.")

        st.markdown('<div class="panel-title">Recent Claim Activity</div>', unsafe_allow_html=True)
        if not billing_df.empty:
            recent = billing_df.sort_values("date", ascending=False).head(12).copy()
            recent["claim_status"] = recent["status"].apply(status_pill)
            recent["amount"] = recent["amount"].map(lambda value: f"${value:,.2f}")
            recent["date"] = recent["date"].dt.strftime("%Y-%m-%d %H:%M")
            display_columns = ["date", "patient_name", "cpt_code", "diagnosis_code", "amount", "claim_status"]
            st.markdown(recent[display_columns].to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No claims to display.")

    with tabs[1]:
        left, right = st.columns([1.1, 1])
        with left:
            st.markdown('<div class="panel-title">Revenue by Procedure</div>', unsafe_allow_html=True)
            if not billing_df.empty:
                top_procedures = (
                    billing_df.groupby(["cpt_code", "description"], as_index=False)["amount"]
                    .sum()
                    .sort_values("amount", ascending=False)
                    .head(8)
                )
                fig = px.bar(
                    top_procedures,
                    x="amount",
                    y="cpt_code",
                    orientation="h",
                    color="amount",
                    color_continuous_scale=["#dbeafe", "#0f766e"],
                )
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data yet.")

        with right:
            st.markdown('<div class="panel-title">Denials by Diagnosis</div>', unsafe_allow_html=True)
            if not billing_df.empty:
                denied = billing_df[billing_df["status"] == "denied"]
                if not denied.empty:
                    denied_summary = denied.groupby("diagnosis_code", as_index=False).size().sort_values("size", ascending=False).head(8)
                    fig = px.bar(
                        denied_summary,
                        x="diagnosis_code",
                        y="size",
                        color="size",
                        color_continuous_scale=["#fee2e2", "#b91c1c"],
                    )
                    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No denied claims.")
            else:
                st.info("No denial data yet.")

        if not billing_df.empty:
            st.markdown('<div class="panel-title">Flagged Claims Queue</div>', unsafe_allow_html=True)
            flagged = billing_df[billing_df["is_flagged"].fillna(False)].copy()
            if flagged.empty:
                st.success("No claims are currently flagged.")
            else:
                flagged["date"] = flagged["date"].dt.strftime("%Y-%m-%d")
                flagged["amount"] = flagged["amount"].map(lambda value: f"${value:,.2f}")
                st.dataframe(
                    flagged[["date", "patient_name", "cpt_code", "diagnosis_code", "amount", "anomaly_score"]],
                    use_container_width=True,
                    hide_index=True,
                )

    with tabs[2]:
        st.markdown('<div class="panel-title">Patient Directory</div>', unsafe_allow_html=True)
        if not patients_df.empty:
            search = st.text_input("Search patient", placeholder="Name, insurance, or email")
            directory = patients_df.copy()
            if search:
                mask = directory.astype(str).apply(lambda column: column.str.contains(search, case=False, na=False))
                directory = directory[mask.any(axis=1)]
            st.dataframe(
                directory[["first_name", "last_name", "insurance_type", "insurance_provider", "email", "phone"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No patients in the directory.")

        with st.expander("Add patient", expanded=False):
            with st.form("add_patient"):
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("First Name")
                    dob = st.date_input("Date of Birth")
                    insurance_type = st.selectbox("Insurance Type", ["Private", "Medicare", "Medicaid", "Self-pay"])
                    email = st.text_input("Email")
                with c2:
                    last_name = st.text_input("Last Name")
                    insurance_provider = st.text_input("Insurance Provider")
                    phone = st.text_input("Phone")
                submitted = st.form_submit_button("Save Patient", use_container_width=True)
                if submitted:
                    payload = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "date_of_birth": str(dob),
                        "insurance_provider": insurance_provider,
                        "insurance_type": insurance_type,
                        "email": email or None,
                        "phone": phone or None,
                    }
                    status_code, body = api_post("/patients/", payload)
                    if status_code in {200, 201}:
                        st.success("Patient saved.")
                        st.rerun()
                    else:
                        st.error(body.get("detail", body))

    with tabs[3]:
        st.markdown('<div class="panel-title">Create Claim</div>', unsafe_allow_html=True)
        if patients_df.empty or procedures_df.empty:
            st.warning("Seed patients and procedures first.")
        else:
            patient_options = {
                f"{row['first_name']} {row['last_name']} | {row['insurance_type']}": row["id"]
                for _, row in patients_df.iterrows()
            }
            procedure_options = {
                f"{row['cpt_code']} | {row['description']}": row["id"]
                for _, row in procedures_df.iterrows()
            }

            with st.form("create_claim"):
                c1, c2 = st.columns(2)
                with c1:
                    patient_label = st.selectbox("Patient", list(patient_options.keys()))
                    amount = st.number_input("Billed Amount", min_value=1.0, value=195.0, step=5.0)
                with c2:
                    procedure_label = st.selectbox("Procedure", list(procedure_options.keys()))
                    status = st.selectbox("Status", ["pending", "paid", "denied"])
                diagnosis_code = st.text_input("Diagnosis Code", value="I10")
                submitted = st.form_submit_button("Create Claim", use_container_width=True)

                if submitted:
                    payload = {
                        "patient_id": patient_options[patient_label],
                        "procedure_id": procedure_options[procedure_label],
                        "amount": float(amount),
                        "status": status,
                        "diagnosis_code": diagnosis_code.strip().upper() or None,
                    }
                    status_code, body = api_post("/billing/", payload)
                    if status_code in {200, 201}:
                        st.success("Claim created.")
                        st.rerun()
                    else:
                        st.error(body.get("detail", body))


inject_theme()

if not st.session_state.token:
    render_marketing_shell()
else:
    render_sidebar()
    render_dashboard()
