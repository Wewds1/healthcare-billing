# 🏥 Healthcare Billing AI System — Portfolio Upgrade Roadmap

> **Target:** ML/AI Engineer Portfolio Project  
> **Timeline:** 7 Days (Full Sprint — 8+ hrs/day)  
> **Stack:** FastAPI · PostgreSQL · Streamlit · Docker · Scikit-learn · OpenCV · Tesseract · Ollama · Render  
> **Current State:** Functional CRUD app with JWT auth, Docker, Alembic migrations, Streamlit dashboard  
> **Target State:** Production-grade AI-powered healthcare billing platform with 4 ML/AI modules

---

## 🎯 What Recruiters Will See (Priority Order)

| # | Feature | Signal to Recruiter |
|---|---------|-------------------|
| 1 | **ML Claim Denial Predictor** | You can build, train, and deploy real ML models on domain data |
| 2 | **OCR Document Scanner** | OpenCV + Tesseract pipeline on real document types |
| 3 | **Live Cloud Deployment on Render** | You ship working software, not just notebooks |
| 4 | **Clean Code Architecture** | You write production-quality, maintainable code |

---

## 🗂️ New Project Structure (After Upgrade)

```
healthcare-billing/
│
├── app/                          # FastAPI backend (existing, upgraded)
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── crud/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── billing_record.py
│   │   ├── patient.py
│   │   ├── procedure.py
│   │   ├── user.py
│   │   ├── ml_predict.py         # NEW — ML prediction endpoints
│   │   └── ocr.py                # NEW — OCR document upload endpoints
│   └── core/
│       ├── security.py
│       └── dependencies.py
│
├── ml/                           # NEW — All ML/AI code lives here
│   ├── data/
│   │   ├── generate_synthetic.py # Synthetic dataset generator
│   │   └── synthetic_billing.csv # Generated training data (~5,000 records)
│   ├── models/
│   │   ├── train_denial_model.py # Training script
│   │   ├── train_anomaly_model.py
│   │   └── saved/                # Serialized .pkl model files
│   │       ├── denial_model.pkl
│   │       ├── denial_scaler.pkl
│   │       └── anomaly_model.pkl
│   └── inference/
│       ├── denial_predictor.py   # Prediction logic (called by router)
│       └── anomaly_detector.py
│
├── ocr/                          # NEW — Document OCR pipeline
│   ├── pipeline.py               # Main OCR orchestration
│   ├── preprocessor.py           # OpenCV image preprocessing
│   ├── extractor.py              # Tesseract text extraction
│   ├── parser.py                 # Field parsing from raw OCR text
│   └── sample_docs/              # Sample documents for demo
│
├── chatbot/                      # NEW — Ollama NLP chatbot
│   ├── agent.py                  # LangChain/Ollama agent
│   ├── tools.py                  # DB query tools for the agent
│   └── prompts.py                # System prompts
│
├── dashboard.py                  # Streamlit app (heavily upgraded)
├── pages/                        # NEW — Streamlit multi-page
│   ├── 1_Dashboard.py
│   ├── 2_Patients.py
│   ├── 3_Billing.py
│   ├── 4_ML_Predictor.py         # NEW
│   ├── 5_OCR_Scanner.py          # NEW
│   ├── 6_AI_Chatbot.py           # NEW
│   └── 7_Analytics.py            # NEW — Upgraded charts
│
├── tests/                        # NEW — Test suite
│   ├── test_api.py
│   ├── test_ml.py
│   └── test_ocr.py
│
├── scripts/
│   └── seed_data.py              # Existing, upgraded
│
├── docker-compose.yml            # Upgraded — adds Streamlit + Ollama services
├── Dockerfile.api                # FastAPI container
├── Dockerfile.streamlit          # NEW — Streamlit container
├── render.yaml                   # Render deployment config
├── requirements.txt              # Upgraded
├── requirements-ml.txt           # NEW — ML-specific deps
├── .env
├── .env.example                  # NEW — safe to commit
├── .github/
│   └── workflows/
│       └── ci.yml                # NEW — GitHub Actions CI
└── README.md                     # Fully rewritten, portfolio-grade
```

---

## 📅 7-Day Sprint Plan

---

### DAY 1 — Foundation & Synthetic Data
**Goal:** Clean up the existing codebase and generate training data for all ML models

#### Morning (4 hrs): Codebase Cleanup
- [ ] Fix CORS: replace `allow_origins=["*"]` with environment-based whitelist
- [ ] Add role-based access control (RBAC) guards to all routers — admin vs doctor vs billing staff
- [ ] Add `email` and `phone` fields to Patient model (currently missing)
- [ ] Add `diagnosis_code` (ICD-10) field to BillingRecord model — critical for ML features
- [ ] Add `insurance_type` field to Patient — will be a key ML feature
- [ ] Run Alembic migration for new fields
- [ ] Containerize Streamlit in `docker-compose.yml` (currently runs outside Docker)
- [ ] Add health checks to Docker services

#### Afternoon (4 hrs): Synthetic Data Generator
Build `ml/data/generate_synthetic.py` that produces a realistic CSV dataset (~5,000 rows).

**Target columns for the CSV:**

| Column | Type | Notes |
|--------|------|-------|
| `patient_age` | int | 18–90 |
| `insurance_type` | categorical | Medicare, Medicaid, Private, Self-pay |
| `procedure_cpt_code` | categorical | 20 real CPT codes |
| `diagnosis_code` | categorical | 15 ICD-10 codes |
| `billed_amount` | float | Realistic ranges per procedure |
| `days_since_last_claim` | int | Patient claim history |
| `num_prior_claims` | int | Per patient |
| `prior_denial_rate` | float | 0.0–1.0 |
| `claim_status` | binary | **Target variable**: 0=paid, 1=denied |
| `anomaly_label` | binary | For anomaly detection training |

**Denial logic to encode (realistic rules):**
- Self-pay → 40% denial rate
- Medicaid + high-cost procedure → 35% denial
- >3 claims in 30 days → 50% denial
- Mismatched diagnosis/procedure codes → 60% denial
- Add controlled noise (12%) so model doesn't overfit

**Anomaly logic to encode:**
- Amount > 3x median for that CPT code
- Same patient, same procedure, within 7 days
- Amount = $0 or > $50,000
- Inject ~8% anomaly rate

#### Day 1 Deliverables
- ✅ Clean, role-guarded FastAPI backend
- ✅ Streamlit running inside Docker
- ✅ `synthetic_billing.csv` with ~5,000 records
- ✅ All new DB fields migrated

---

### DAY 2 — ML Model 1: Claim Denial Predictor
**Goal:** Train, evaluate, and serve a claim denial prediction model

#### Morning (4 hrs): Model Training
File: `ml/models/train_denial_model.py`

**Pipeline:**
```
Raw CSV
  → pandas preprocessing (encode categoricals, scale numerics)
  → Train/test split (80/20, stratified on claim_status)
  → Try 3 models: LogisticRegression, RandomForest, GradientBoosting
  → Compare: Accuracy, Precision, Recall, F1, ROC-AUC
  → Select best (expect GradientBoosting ~0.82–0.87 AUC)
  → Serialize: model.pkl + scaler.pkl
  → Save feature importance plot
  → Save confusion matrix
  → Save classification report as JSON
```

**Why this matters for your portfolio:** You're not just training — you're building a comparison pipeline showing model selection methodology, which is real ML engineering.

**Key metrics to log:**
- ROC-AUC (primary — handles class imbalance)
- Precision/Recall tradeoff (healthcare context: false negatives = missed denials = lost revenue)
- Feature importances — `prior_denial_rate` and `insurance_type` should rank highest

#### Afternoon (4 hrs): FastAPI Inference Endpoint
File: `app/routers/ml_predict.py`

**Endpoints to build:**

```
POST /ml/predict/denial
  Input:  { patient_id, procedure_id, insurance_type, diagnosis_code, ... }
  Output: { denial_probability: 0.73, risk_level: "HIGH", top_risk_factors: [...] }

GET /ml/model/info
  Output: { model_type, training_date, accuracy, auc_score, feature_count }

POST /ml/predict/batch
  Input:  List of billing records
  Output: List of predictions with risk scores
```

**Important:** Load model at startup using FastAPI `lifespan` context (not on every request).

**Streamlit page** (`pages/4_ML_Predictor.py`):
- Input form: patient info + procedure
- Show prediction with probability gauge (st.progress or plotly gauge chart)
- Show top 3 risk factors driving the prediction
- "What-if" sliders: change insurance type or diagnosis, see probability shift live

#### Day 2 Deliverables
- ✅ Trained model with documented metrics (AUC ≥ 0.80)
- ✅ `/ml/predict/denial` endpoint live
- ✅ Streamlit prediction page with risk gauge
- ✅ Feature importance chart

---

### DAY 3 — ML Model 2: Anomaly Detection
**Goal:** Detect fraudulent/erroneous billing entries using unsupervised + supervised methods

#### Morning (4 hrs): Anomaly Detection Pipeline
File: `ml/models/train_anomaly_model.py`

**Two-layer approach (this is what makes it portfolio-worthy):**

**Layer 1 — Unsupervised (Isolation Forest):**
- Train on all billing records
- No labels needed — learns "normal" billing patterns
- Flags statistical outliers
- Produces anomaly score (-1 = anomaly, 1 = normal)

**Layer 2 — Rule-Based Post-filter:**
- Duplicate claim within 7 days: same patient + same CPT
- Amount deviation: > 2.5 std deviations from mean for that CPT code
- Zero-dollar claims flagged as suspicious
- Combine: if Isolation Forest flags AND rule matches → HIGH confidence anomaly

**Evaluation:**
- Use the `anomaly_label` column from synthetic data
- Report precision, recall at different contamination thresholds
- Plot anomaly score distribution

#### Afternoon (4 hrs): Integration + Streamlit Page
File: `app/routers/ml_predict.py` (add to existing)

**New endpoints:**
```
GET  /ml/anomalies                    — All flagged records
POST /ml/anomalies/scan               — Scan new billing record on create
GET  /ml/anomalies/{record_id}        — Anomaly details for a record
```

**Auto-scan on billing creation:** Modify `POST /billing/` to automatically run anomaly check and store `anomaly_score` + `is_flagged` on the BillingRecord model.

**Streamlit page** (`pages/7_Analytics.py` — upgrade existing Reports tab):
- Anomaly score distribution histogram
- Table of flagged records with risk scores, sortable
- Map of anomaly types (duplicate, amount outlier, etc.)
- Revenue at risk metric: total billed amount of flagged records

#### Day 3 Deliverables
- ✅ Isolation Forest model trained and serialized
- ✅ Auto-scan on every new billing record
- ✅ Flagged records dashboard
- ✅ Revenue-at-risk metric visible

---

### DAY 4 — OCR Document Scanner (Your OpenCV Showcase)
**Goal:** Upload a document image/PDF, extract billing fields automatically using OpenCV + Tesseract

This is where your OpenCV background becomes a direct portfolio differentiator.

#### Morning (4 hrs): OpenCV Preprocessing Pipeline
File: `ocr/preprocessor.py`

**Pipeline per document type:**

```
Raw Image/PDF
  ↓
[1] Load & Normalize
    - pdf2image for PDF → image conversion
    - Resize to standard DPI (300 DPI target)

[2] Deskew (OpenCV)
    - Detect rotation using Hough Line Transform
    - Rotate to correct skew angle (common in scanned docs)

[3] Denoise
    - cv2.fastNlMeansDenoising() for grayscale
    - Bilateral filter for edge preservation

[4] Binarization
    - Adaptive thresholding (better than global for uneven lighting)
    - cv2.adaptiveThreshold(ADAPTIVE_THRESH_GAUSSIAN_C)

[5] Border/Shadow Removal
    - Morphological operations to remove dark borders
    - Shadow normalization via local histogram equalization

[6] Region of Interest Detection
    - Contour detection to find text regions
    - Filter by area to eliminate noise contours
    - Returns list of (x, y, w, h) bounding boxes

Output: cleaned image + ROI bounding boxes
```

File: `ocr/extractor.py`

```python
# Tesseract config per document type
CONFIGS = {
    "insurance_claim": "--psm 6 --oem 3",  # uniform block of text
    "invoice":         "--psm 4 --oem 3",  # single column
    "patient_id":      "--psm 7 --oem 3",  # single line
    "handwritten":     "--psm 6 --oem 1",  # LSTM engine for handwriting
}
```

#### Afternoon (4 hrs): Field Parser + FastAPI + Streamlit
File: `ocr/parser.py`

**Regex + pattern extraction for each document type:**

| Document Type | Fields to Extract |
|--------------|------------------|
| Insurance Claim Form | Patient name, DOB, insurance ID, CPT codes, ICD-10 codes, billed amount, provider NPI |
| Hospital Invoice | Invoice number, date, line items (procedure + amount), total, tax |
| Patient ID Card | Member ID, group number, patient name, effective date, copay amounts |
| Handwritten Notes | Flag as "manual review required", extract any numbers found |

**FastAPI endpoint** (`app/routers/ocr.py`):
```
POST /ocr/upload
  Input:  multipart/form-data — image or PDF file + document_type
  Output: {
    extracted_fields: { patient_name, dob, insurance_id, cpt_codes: [], amounts: [] },
    confidence_scores: { field: score },
    raw_text: "...",
    preprocessed_image_url: "..."   ← base64 or saved file
  }

POST /ocr/upload-and-create
  — Runs OCR then auto-populates a new BillingRecord from extracted fields
```

**Streamlit page** (`pages/5_OCR_Scanner.py`):
- File uploader (image or PDF)
- Document type selector dropdown
- Show: original image vs preprocessed image (side by side) — **this is your OpenCV showcase moment**
- Show extracted fields with confidence scores (color coded: green/yellow/red)
- Editable fields — user can correct OCR errors before saving
- "Save to Billing Record" button

#### Day 4 Deliverables
- ✅ Full OpenCV preprocessing pipeline (deskew, denoise, binarize)
- ✅ Tesseract extraction with per-document configs
- ✅ Field parser for all 4 document types
- ✅ OCR Streamlit page with before/after image comparison
- ✅ Auto-populate billing record from OCR output

---

### DAY 5 — NLP Chatbot with Ollama
**Goal:** Local AI chatbot that can answer questions about billing data using natural language

#### Morning (4 hrs): Ollama Agent Setup
**Model to use:** `llama3.2` (3B — fast, runs on CPU, good reasoning)  
**Fallback:** `phi3:mini` if hardware is limited

File: `chatbot/tools.py` — Define tools the agent can call:

```python
# Tool 1: Query billing summary
def get_billing_summary(date_range: str, status: str) -> dict:
    """Returns revenue stats, record counts, avg amounts"""

# Tool 2: Patient lookup
def get_patient_billing_history(patient_name_or_id: str) -> list:
    """Returns all billing records for a patient"""

# Tool 3: Anomaly report
def get_flagged_records(limit: int = 10) -> list:
    """Returns most recent anomaly-flagged records"""

# Tool 4: Denial risk check
def check_denial_risk(patient_id: int, procedure_cpt: str) -> dict:
    """Calls ML model and returns risk assessment"""

# Tool 5: Procedure cost lookup
def get_procedure_info(cpt_code: str) -> dict:
    """Returns procedure description, average cost, denial rate"""
```

File: `chatbot/agent.py`:
- Use Ollama Python library (`ollama.chat()`)
- Implement simple ReAct pattern: model decides which tool to call, gets result, forms answer
- Keep conversation history in session (last 10 turns)
- Add guardrails: chatbot only answers billing-related questions

#### Afternoon (4 hrs): Streamlit Chatbot Page
File: `pages/6_AI_Chatbot.py`

**UI Design:**
- Chat interface with `st.chat_message` components
- Typing indicator while Ollama responds
- Show tool calls as expandable "Reasoning" sections (transparency)
- Suggested questions: "What's our denial rate this month?", "Show me flagged claims", "What's the risk for CPT 99213?"
- Clear conversation button

**Example conversations to demo:**
```
User: "How much revenue did we collect last month?"
Bot: [calls get_billing_summary] → "Last month: $142,300 collected across 87 paid claims..."

User: "Which patients have the highest denial risk?"
Bot: [calls get_patient_billing_history + check_denial_risk] → "3 patients flagged high risk..."

User: "Show me any suspicious billing records"
Bot: [calls get_flagged_records] → "Found 4 anomalous records: [details]..."
```

#### Day 5 Deliverables
- ✅ Ollama running in Docker (add to docker-compose)
- ✅ 5 DB-connected tools implemented
- ✅ ReAct agent with conversation memory
- ✅ Streamlit chatbot UI with reasoning transparency

---

### DAY 6 — Analytics Dashboard Upgrade + Tests
**Goal:** Replace basic Streamlit bar charts with a portfolio-grade analytics dashboard, and add tests

#### Morning (3 hrs): Upgraded Analytics (pages/7_Analytics.py)

Replace all `st.bar_chart()` with Plotly interactive charts:

**Chart 1 — Revenue Trend (Line chart):**
- Monthly revenue over time
- Separate lines: billed vs collected vs denied
- Plotly with hover tooltips

**Chart 2 — Denial Rate by Insurance Type (Grouped bar):**
- X-axis: insurance types
- Y-axis: denial %
- Color: procedure category

**Chart 3 — Anomaly Score Distribution (Histogram):**
- All billing records plotted by anomaly score
- Red vertical line at threshold
- Flagged records highlighted

**Chart 4 — Procedure Revenue Breakdown (Treemap):**
- Size = total revenue per CPT code
- Color = denial rate
- Interactive: click to drill down

**Chart 5 — Patient Risk Matrix (Scatter):**
- X-axis: claim frequency
- Y-axis: denial rate
- Size: total billed
- Color: risk tier (low/medium/high)
- Hover: patient name, insurance type

**KPI Cards Row (top of page):**
- Total Revenue | Collection Rate | Denial Rate | Anomalies Flagged | Avg Claim Value

#### Midday (3 hrs): Test Suite
File: `tests/test_api.py`:
- Test all CRUD endpoints with `TestClient`
- Test auth: login, protected routes, invalid tokens
- Test role restrictions: doctor can't access admin routes

File: `tests/test_ml.py`:
- Test denial predictor loads and returns valid probability
- Test anomaly detector flags known anomalies
- Test batch prediction endpoint

File: `tests/test_ocr.py`:
- Test preprocessor on a sample image
- Test field parser with known OCR output string

#### Afternoon (2 hrs): CI/CD Pipeline
File: `.github/workflows/ci.yml`:
```yaml
# On every push to main:
# 1. Run pytest
# 2. Build Docker image (validate it builds)
# 3. If tests pass on main: trigger Render deploy webhook
```

#### Day 6 Deliverables
- ✅ 5 interactive Plotly charts in analytics dashboard
- ✅ KPI cards at top of analytics page
- ✅ 15+ tests covering API, ML, and OCR
- ✅ GitHub Actions CI pipeline

---

### DAY 7 — Cloud Deployment + README + Polish
**Goal:** Deploy to Render, write portfolio README, final polish

#### Morning (3 hrs): Render Deployment

**Architecture on Render:**
```
Render Web Service #1: FastAPI (api/)
  — Dockerfile.api
  — Free tier: 512MB RAM

Render Web Service #2: Streamlit (dashboard)
  — Dockerfile.streamlit
  — Free tier

Render PostgreSQL: Managed DB
  — Free tier (90 days) or $7/mo starter

Note: Ollama cannot run on Render free tier
  — Solution: Disable Ollama in cloud, use a simple
    rule-based fallback OR OpenAI API as optional backend
  — Show Ollama as "local mode" in README
```

File: `render.yaml` (upgrade existing):
```yaml
services:
  - type: web
    name: hbs-api
    env: docker
    dockerfilePath: ./Dockerfile.api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: hbs-db
          property: connectionString
  
  - type: web
    name: hbs-dashboard
    env: docker
    dockerfilePath: ./Dockerfile.streamlit
    envVars:
      - key: API_URL
        value: https://hbs-api.onrender.com

databases:
  - name: hbs-db
    databaseName: billing_db
    plan: free
```

#### Midday (3 hrs): Portfolio README
File: `README.md` — this is a recruiter's first impression.

**Sections:**
1. **Header** — Project name, live demo link badge, tech stack badges
2. **What This Does** — 2-paragraph plain English description
3. **Architecture Diagram** — ASCII or Mermaid diagram of system components
4. **ML/AI Features** — Detailed explanation of each model with metrics
   - Claim Denial Predictor: show AUC score, confusion matrix image
   - Anomaly Detection: show precision/recall, example flagged records
   - OCR Pipeline: show before/after preprocessing images
   - NLP Chatbot: GIF or screenshot of conversation
5. **Tech Stack Table** — Every technology with why it was chosen
6. **Local Setup** — Step-by-step Docker commands
7. **API Documentation** — Link to `/docs` on live instance
8. **Data** — Explain synthetic data generation methodology
9. **Testing** — How to run tests, current coverage
10. **Roadmap** — What you'd add with more time (shows product thinking)

#### Afternoon (2 hrs): Final Polish
- [ ] Add loading spinners to all Streamlit pages
- [ ] Add error states (when API is down, show user-friendly message)
- [ ] Add `st.cache_data` to expensive API calls
- [ ] Add page-level access control in Streamlit (doctor vs admin sees different pages)
- [ ] Generate 50 realistic seed records using the synthetic data generator
- [ ] Record a 3-minute demo video walkthrough
- [ ] Verify all Docker services start cleanly with `docker compose up`

#### Day 7 Deliverables
- ✅ Live URL on Render
- ✅ Portfolio-grade README with screenshots/metrics
- ✅ All Docker services cleanly orchestrated
- ✅ Demo video recorded

---

## 🧰 Full Technology Stack (After Upgrade)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend API** | FastAPI | REST API, async, auto-docs |
| **Database** | PostgreSQL 15 | Primary data store |
| **ORM** | SQLAlchemy 2.0 | DB abstraction |
| **Migrations** | Alembic | Schema versioning |
| **Auth** | JWT (python-jose) | Stateless authentication |
| **Frontend** | Streamlit | Multi-page dashboard |
| **Charts** | Plotly | Interactive visualizations |
| **ML — Classification** | Scikit-learn (GradientBoostingClassifier) | Denial prediction |
| **ML — Anomaly** | Scikit-learn (IsolationForest) | Fraud/error detection |
| **OCR — Preprocessing** | OpenCV (cv2) | Image cleanup pipeline |
| **OCR — Extraction** | Tesseract / pytesseract | Text extraction |
| **OCR — PDF** | pdf2image / Pillow | PDF to image conversion |
| **NLP Chatbot** | Ollama (llama3.2) | Local LLM inference |
| **Containerization** | Docker + Docker Compose | Full service orchestration |
| **Deployment** | Render | Cloud hosting |
| **CI/CD** | GitHub Actions | Automated testing + deploy |
| **Testing** | pytest + httpx | API and ML test suite |

---

## 📦 Updated requirements.txt

```
# Existing
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pandas==2.1.3
python-dotenv==1.0.0
pydantic==2.5.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-jose[cryptography]==3.3.0
alembic==1.12.1
streamlit>=1.32.0

# ML (requirements-ml.txt — separate for lighter API container)
scikit-learn==1.4.0
numpy==1.26.0
joblib==1.3.2
imbalanced-learn==0.11.0    # SMOTE for class imbalance

# OCR
opencv-python-headless==4.9.0.80
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.2.0

# Charts
plotly==5.18.0

# Chatbot
ollama==0.1.7

# Testing
pytest==7.4.3
httpx==0.25.2               # For async FastAPI test client

# Utilities
python-multipart==0.0.6     # File upload support
aiofiles==23.2.1
```

---

## 🤔 Key Technical Decisions Explained

### Why Gradient Boosting over Neural Networks for Denial Prediction?
With ~5,000 synthetic records, a neural network would overfit. GradientBoosting (or XGBoost) achieves better AUC on tabular data at this scale, trains in seconds, and produces easily interpretable feature importances — exactly what a billing team needs to act on predictions.

### Why Isolation Forest for Anomaly Detection?
Healthcare billing anomalies are rare (~5-8% of claims). Isolation Forest is designed for exactly this: it doesn't need labels, works well with rare events, and is fast at inference — suitable for real-time scanning on every claim creation.

### Why Ollama (local) over OpenAI API?
For a portfolio project targeting ML/AI engineering roles: showing you can run inference locally demonstrates understanding of model deployment and hardware considerations — a more impressive signal than "I called an API." You also avoid any API costs and data privacy concerns with patient data.

### Why Two Dockerfiles (API + Streamlit)?
Separation of concerns: the API and dashboard can scale independently and be deployed as separate Render services. This mirrors real production architecture where frontend and backend are decoupled.

---

## 📊 Expected ML Metrics (Realistic Targets)

| Model | Metric | Expected Range | Notes |
|-------|--------|---------------|-------|
| Denial Predictor | ROC-AUC | 0.82 – 0.88 | Using GradientBoosting |
| Denial Predictor | F1 Score | 0.74 – 0.82 | After SMOTE balancing |
| Denial Predictor | Precision | 0.78 – 0.85 | Focus on minimizing false negatives |
| Anomaly Detector | Precision | 0.70 – 0.80 | At contamination=0.08 |
| Anomaly Detector | Recall | 0.75 – 0.85 | Catching real anomalies matters most |
| OCR Extraction | Field Accuracy | 85–95% | On clean printed documents |
| OCR Extraction | Field Accuracy | 60–75% | On handwritten notes (expected lower) |

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Tesseract struggles with handwritten notes | Clearly label accuracy limitations in UI; add "manual review" flag |
| Ollama too slow on CPU for demo | Use `phi3:mini` (smaller model) or pre-generate example responses for screenshots |
| Render free tier cold starts (30s delay) | Add loading page in Streamlit explaining cold start; or use UptimeRobot to ping every 10min |
| ML model underperforms on synthetic data | Tune contamination and decision thresholds; document the tradeoff explicitly in README |
| OCR page layout varies across document types | Build type-specific parsing configs; add confidence score so user knows when to manually correct |

---

## 🚀 After This Week — What to Add Next

These are intentionally left out to keep the 1-week scope realistic, but mentioning them in your README shows product thinking:

- **FHIR API integration** — real HL7 FHIR standard for healthcare data exchange
- **Real-time streaming** — Kafka or Redis pub/sub for live billing events
- **Custom model training UI** — upload your own data, retrain in-app
- **Multi-tenancy** — multiple hospital clients on one platform
- **Explainability (SHAP)** — per-prediction SHAP waterfall charts
- **PDF report generation** — export billing summaries as formatted PDFs
- **Insurance eligibility API** — integrate with real payer APIs

---

## ✅ Definition of Done

The project is portfolio-ready when:

- [ ] `docker compose up` starts all services cleanly in under 60 seconds
- [ ] ML denial predictor returns a prediction with probability and risk factors
- [ ] OCR page accepts an uploaded image, shows preprocessed result, extracts fields
- [ ] Chatbot answers at least 5 types of billing questions using real DB data
- [ ] Analytics page has ≥ 5 interactive Plotly charts
- [ ] Live URL accessible on Render (may have cold start — that's fine)
- [ ] README includes live link, architecture diagram, and ML metrics with screenshots
- [ ] `pytest tests/` passes with ≥ 15 tests
- [ ] GitHub Actions CI runs on every push

---

*Generated: Healthcare Billing AI System Portfolio Roadmap — Sprint Week Plan*  
*Stack: FastAPI · PostgreSQL · Streamlit · Scikit-learn · OpenCV · Tesseract · Ollama · Docker · Render*
