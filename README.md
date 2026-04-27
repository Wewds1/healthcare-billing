# Helix Healthcare Billing

Helix is a healthcare billing demo built for portfolio presentation and technical review. It combines a FastAPI backend, a Streamlit operations workspace, OCR-assisted intake hooks, and a denial-risk model trained on a richer synthetic claims dataset.

## What changed

- Local startup is no longer blocked by the Docker-only `db` hostname. Outside Docker, the app falls back to a local SQLite database.
- The API now creates tables on startup, reports real database and ML health, and fixes broken procedure update behavior.
- Billing anomaly checks use real patient and prior-claim context instead of hard-coded placeholder values.
- The seeded dataset is larger and idempotent, so rerunning the seed script does not spam duplicate records.
- The denial model now trains on `120,000` synthetic claims with stronger claim context:
  - place of service
  - claim type
  - network status
  - authorization coverage
  - billed units
- The Streamlit UI was rebuilt into a more deliberate product surface for demos and portfolio screenshots.

## Stack

- FastAPI
- SQLAlchemy
- Streamlit
- scikit-learn
- PostgreSQL or SQLite
- OCR pipeline hooks for document ingestion

## Quick start

### Local demo mode

1. Install dependencies from `requirements.txt`.
2. Start the API:

```bash
uvicorn app.main:app --reload
```

3. Seed demo data:

```bash
python app/scripts/seed_data.py
```

4. Start the Streamlit workspace:

```bash
streamlit run dashboard.py
```

If `DATABASE_URL` points at the Docker service host `db`, the app automatically falls back to `sqlite:///./healthcare_billing.db` for a normal local run.

### Docker mode

```bash
docker compose up --build
```

## Demo credentials

- `admin / adminadmin`
- `doctor1 / Doctor123!`
- `billing_staff / Staff123!`

## ML model snapshot

Current denial model artifact:

- model: `Gradient Boosting`
- training rows: `120,000`
- encoded features: `53`
- ROC-AUC: `0.7905`

This is still synthetic-data modeling, so it is useful for demo realism and system design review, not for claiming real production clinical or financial performance.

## Portfolio framing

This project now presents cleanly as:

- a healthcare revenue-cycle operations dashboard
- a denial-risk triage workflow
- an OCR-to-claim ingestion prototype
- a full-stack demo with API, data, ML, and UI layers

## Main paths

- API entry: [app/main.py](/D:/healthcare-billing/app/main.py)
- dashboard: [dashboard.py](/D:/healthcare-billing/dashboard.py)
- denial model training: [ml/models/train_model_denial.py](/D:/healthcare-billing/ml/models/train_model_denial.py)
- synthetic data generation: [ml/data/generate_synthetic.py](/D:/healthcare-billing/ml/data/generate_synthetic.py)
- seed script: [app/scripts/seed_data.py](/D:/healthcare-billing/app/scripts/seed_data.py)
