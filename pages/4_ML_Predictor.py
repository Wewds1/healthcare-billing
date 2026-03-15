import os
import requests
import streamlit as st
import plotly.graph_objects as go

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="ML Claim Denial Predictor", page_icon="ML", layout="wide")

# Reuse auth session from your main app
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def auth_headers() -> dict:
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_get(path: str):
    try:
        resp = requests.get(f"{API_URL}{path}", headers=auth_headers(), timeout=20)
        content_type = resp.headers.get("content-type", "")
        body = resp.json() if "application/json" in content_type else resp.text
        return resp.status_code, body
    except requests.RequestException as exc:
        return 0, {"detail": str(exc)}


def api_post(path: str, payload: dict):
    try:
        resp = requests.post(f"{API_URL}{path}", json=payload, headers=auth_headers(), timeout=30)
        content_type = resp.headers.get("content-type", "")
        body = resp.json() if "application/json" in content_type else resp.text
        return resp.status_code, body
    except requests.RequestException as exc:
        return 0, {"detail": str(exc)}


def risk_color(level: str) -> str:
    level = (level or "").upper()
    if level == "HIGH":
        return "#b42318"
    if level == "MEDIUM":
        return "#b54708"
    return "#027a48"


def render_gauge(probability: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(probability * 100, 2),
            number={"suffix": "%"},
            title={"text": "Denial Probability"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 40], "color": "#e8f5e9"},
                    {"range": [40, 70], "color": "#fff7e6"},
                    {"range": [70, 100], "color": "#fdecea"},
                ],
                "threshold": {"line": {"color": "#111827", "width": 3}, "thickness": 0.8, "value": 70},
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


st.title("Claim Denial Predictor")
st.caption("Day 2 UI: single prediction, model info, and what-if analysis")

if not st.session_state.token:
    st.warning("Login first from the main dashboard page to use ML endpoints.")
    st.stop()

# Health + model info row
col_a, col_b = st.columns([1, 2])

with col_a:
    st.subheader("Service Status")
    ml_health_status, ml_health = api_get("/ml/health")
    if ml_health_status == 200 and isinstance(ml_health, dict):
        st.success(f"ML service: {ml_health.get('status', 'unknown')}")
        st.write(f"Model loaded: {ml_health.get('model_loaded')}")
        st.write(f"Model type: {ml_health.get('model_type')}")
    else:
        st.error("ML service unavailable")
        st.write(ml_health)

with col_b:
    st.subheader("Model Info")
    info_status, info_body = api_get("/ml/model/info")
    if info_status == 200 and isinstance(info_body, dict):
        c1, c2, c3, c4 = st.columns(4)
        metrics = info_body.get("metrics", {})
        c1.metric("Model", info_body.get("model_type", "N/A"))
        c2.metric("AUC", f"{metrics.get('roc_auc', 0):.3f}" if isinstance(metrics, dict) else "N/A")
        c3.metric("Features", info_body.get("num_features", "N/A"))
        c4.metric("Training Rows", info_body.get("training_data_size", "N/A"))
        st.caption(f"Trained: {info_body.get('training_date', 'N/A')}")
    else:
        st.error("Failed to load model info")
        st.write(info_body)

st.markdown("---")

# Input + result layout
left, right = st.columns([1, 1])

with left:
    st.subheader("Prediction Input")
    with st.form("predict_form", clear_on_submit=False):
        patient_age = st.slider("Patient Age", min_value=0, max_value=100, value=65)
        insurance_type = st.selectbox("Insurance Type", ["Medicare", "Medicaid", "Private", "Self-pay"])
        procedure_cpt_code = st.text_input("Procedure CPT Code", value="99214").strip()
        diagnosis_code = st.text_input("Diagnosis Code", value="E11.9").strip().upper()
        billed_amount = st.number_input("Billed Amount", min_value=1.0, value=250.0, step=10.0)
        days_since_last_claim = st.number_input("Days Since Last Claim", min_value=0, value=45, step=1)
        num_prior_claims = st.number_input("Number of Prior Claims", min_value=0, value=3, step=1)
        prior_denial_rate = st.slider("Prior Denial Rate", min_value=0.0, max_value=1.0, value=0.33, step=0.01)

        submitted = st.form_submit_button("Run Prediction")

    payload = {
        "patient_age": int(patient_age),
        "insurance_type": insurance_type,
        "procedure_cpt_code": procedure_cpt_code,
        "diagnosis_code": diagnosis_code,
        "billed_amount": float(billed_amount),
        "days_since_last_claim": int(days_since_last_claim),
        "num_prior_claims": int(num_prior_claims),
        "prior_denial_rate": float(prior_denial_rate),
    }

    if submitted:
        with st.spinner("Scoring claim..."):
            pred_status, pred_body = api_post("/ml/predict/denial", payload)

        if pred_status == 200 and isinstance(pred_body, dict):
            st.session_state["last_payload"] = payload
            st.session_state["last_prediction"] = pred_body
        else:
            st.error("Prediction failed")
            st.write(pred_body)

with right:
    st.subheader("Prediction Result")
    result = st.session_state.get("last_prediction")
    if not result:
        st.info("Submit input to see prediction.")
    else:
        denial_probability = float(result.get("denial_probability", 0.0))
        risk_level = result.get("risk_level", "LOW")
        prediction_label = result.get("prediction_label", "UNKNOWN")
        top_risk_factors = result.get("top_risk_factors", [])

        render_gauge(denial_probability)

        badge_color = risk_color(risk_level)
        st.markdown(
            f"""
            <div style="padding: 0.75rem; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div><strong>Prediction:</strong> {prediction_label}</div>
                <div><strong>Risk Level:</strong> <span style="color:{badge_color}; font-weight:700;">{risk_level}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("Top Risk Factors")
        if top_risk_factors:
            for idx, factor in enumerate(top_risk_factors[:3], start=1):
                name = factor.get("feature", "unknown")
                importance = factor.get("importance", 0.0)
                value = factor.get("value", 0.0)
                st.write(f"{idx}. {name} | importance={importance:.4f} | value={value:.4f}")
        else:
            st.caption("No factor details returned by model.")

st.markdown("---")
st.subheader("What-if Analysis")

base_payload = st.session_state.get("last_payload")
if not base_payload:
    st.info("Run one prediction first to unlock what-if analysis.")
else:
    w1, w2, w3 = st.columns(3)
    with w1:
        wi_insurance = st.selectbox(
            "Change Insurance",
            ["Medicare", "Medicaid", "Private", "Self-pay"],
            index=["Medicare", "Medicaid", "Private", "Self-pay"].index(base_payload["insurance_type"]),
            key="wi_insurance",
        )
    with w2:
        wi_prior_denial = st.slider(
            "Change Prior Denial Rate", 0.0, 1.0, float(base_payload["prior_denial_rate"]), 0.01, key="wi_prior_denial"
        )
    with w3:
        wi_amount = st.number_input(
            "Change Billed Amount", min_value=1.0, value=float(base_payload["billed_amount"]), step=10.0, key="wi_amount"
        )

    if st.button("Recalculate What-if"):
        scenario = dict(base_payload)
        scenario["insurance_type"] = wi_insurance
        scenario["prior_denial_rate"] = float(wi_prior_denial)
        scenario["billed_amount"] = float(wi_amount)

        status_code, body = api_post("/ml/predict/denial", scenario)
        if status_code == 200 and isinstance(body, dict):
            base_prob = float(st.session_state["last_prediction"]["denial_probability"])
            new_prob = float(body["denial_probability"])
            delta = new_prob - base_prob

            c1, c2, c3 = st.columns(3)
            c1.metric("Base Probability", f"{base_prob:.1%}")
            c2.metric("What-if Probability", f"{new_prob:.1%}")
            c3.metric("Delta", f"{delta:+.1%}")
        else:
            st.error("What-if prediction failed")
            st.write(body)