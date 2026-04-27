import os

import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Denial Predictor", page_icon="📈", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None


def auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str):
    try:
        response = requests.get(f"{API_URL}{path}", headers=auth_headers(), timeout=20)
        return response.status_code, response.json() if response.content else {}
    except Exception as exc:
        return 0, {"detail": str(exc)}


def api_post(path: str, payload: dict):
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, headers=auth_headers(), timeout=30)
        return response.status_code, response.json() if response.content else {}
    except Exception as exc:
        return 0, {"detail": str(exc)}


def render_gauge(probability: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(probability * 100, 2),
            number={"suffix": "%"},
            title={"text": "Denial Probability"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#0f766e"},
                "steps": [
                    {"range": [0, 40], "color": "#dcfce7"},
                    {"range": [40, 70], "color": "#fef3c7"},
                    {"range": [70, 100], "color": "#fee2e2"},
                ],
                "threshold": {"line": {"color": "#111827", "width": 3}, "thickness": 0.8, "value": 70},
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


st.title("Denial Risk Workbench")
st.caption("Portfolio-facing claim scoring surface with richer claim context.")

if not st.session_state.token:
    st.warning("Sign in from the main dashboard first.")
    st.stop()

health_status, health_body = api_get("/ml/health")
info_status, info_body = api_get("/ml/model/info")

top_left, top_right = st.columns([1, 1.4])
with top_left:
    st.subheader("Service Health")
    if health_status == 200:
        st.write(health_body)
    else:
        st.error(health_body)
with top_right:
    st.subheader("Model Summary")
    if info_status == 200 and isinstance(info_body, dict):
        metrics = info_body.get("metrics", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Model", info_body.get("model_type", "N/A"))
        c2.metric("AUC", f"{metrics.get('roc_auc', 0):.3f}")
        c3.metric("Rows", f"{info_body.get('training_data_size', 0):,}")
        c4.metric("Threshold", f"{info_body.get('chosen_threshold', 0):.2f}")
        st.caption(f"Top features: {', '.join(info_body.get('top_features', [])[:5])}")
    else:
        st.error(info_body)

st.markdown("---")
left, right = st.columns([1, 1])

with left:
    st.subheader("Score Claim")
    with st.form("predict_form"):
        patient_age = st.slider("Patient Age", 18, 95, 64)
        insurance_type = st.selectbox("Insurance Type", ["Medicare", "Medicaid", "Private", "Self-pay"])
        procedure_cpt_code = st.text_input("Procedure CPT Code", value="99214").strip()
        diagnosis_code = st.text_input("Diagnosis Code", value="E11.9").strip().upper()
        billed_amount = st.number_input("Billed Amount", min_value=1.0, value=250.0, step=10.0)
        days_since_last_claim = st.number_input("Days Since Last Claim", min_value=0, value=45, step=1)
        num_prior_claims = st.number_input("Prior Claims", min_value=0, value=3, step=1)
        prior_denial_rate = st.slider("Prior Denial Rate", 0.0, 1.0, 0.33, 0.01)

        with st.expander("Advanced Claim Context"):
            place_of_service = st.selectbox("Place of Service", ["Office", "Outpatient", "Emergency", "Imaging Center", "Urgent Care"])
            claim_type = st.selectbox("Claim Type", ["Professional", "Institutional"])
            network_status = st.selectbox("Network Status", ["In Network", "Out of Network"])
            authorization_required = st.toggle("Authorization Required", value=False)
            authorization_on_file = st.toggle("Authorization On File", value=True)
            units = st.number_input("Units", min_value=1, max_value=12, value=1, step=1)

        submitted = st.form_submit_button("Run Prediction", use_container_width=True)

    if submitted:
        payload = {
            "patient_age": int(patient_age),
            "insurance_type": insurance_type,
            "procedure_cpt_code": procedure_cpt_code,
            "diagnosis_code": diagnosis_code,
            "billed_amount": float(billed_amount),
            "days_since_last_claim": int(days_since_last_claim),
            "num_prior_claims": int(num_prior_claims),
            "prior_denial_rate": float(prior_denial_rate),
            "place_of_service": place_of_service,
            "claim_type": claim_type,
            "network_status": network_status,
            "authorization_required": int(authorization_required),
            "authorization_on_file": int(authorization_on_file),
            "units": int(units),
        }
        status_code, body = api_post("/ml/predict/denial", payload)
        if status_code == 200:
            st.session_state["last_prediction"] = body
            st.session_state["last_payload"] = payload
        else:
            st.error(body)

with right:
    st.subheader("Prediction Result")
    result = st.session_state.get("last_prediction")
    if not result:
        st.info("Run a score to see the risk profile.")
    else:
        render_gauge(float(result.get("denial_probability", 0.0)))
        st.write(f"Prediction: **{result.get('prediction_label', 'N/A')}**")
        st.write(f"Risk level: **{result.get('risk_level', 'N/A')}**")
        st.write("Top drivers")
        for factor in result.get("top_risk_factors", []):
            st.write(
                f"- `{factor.get('feature')}` | importance={factor.get('importance', 0):.4f} | value={factor.get('value', 0):.4f}"
            )
