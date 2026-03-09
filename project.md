# Healthcare Billing System

## Project Goal

Build a **backend healthcare billing system** using **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**. The system supports CRUD operations for Users, Patients, Procedures, and Billing Records. This project demonstrates automation, data management, and API development, suitable for your portfolio and career in healthcare IT.

---

## File Structure

```
healthcare-billing/
│
├─ app/
│   ├─ __init__.py
│   ├─ main.py           # Entry point of the FastAPI application
│   ├─ database.py       # Connects to PostgreSQL using SQLAlchemy
│   ├─ models/           # SQLAlchemy ORM models
│   │   ├─ __init__.py
│   │   ├─ user.py
│   │   ├─ patient.py
│   │   ├─ procedure.py
│   │   └─ billing_record.py
│   ├─ schemas/          # Pydantic schemas for data validation
│   │   ├─ __init__.py
│   │   ├─ user.py
│   │   ├─ patient.py
│   │   ├─ procedure.py
│   │   └─ billing_record.py
│   ├─ crud/             # Functions to interact with the database
│   │   ├─ __init__.py
│   │   ├─ user.py
│   │   ├─ patient.py
│   │   ├─ procedure.py
│   │   └─ billing_record.py
│   └─ routers/          # FastAPI routers (API endpoints)
│       ├─ __init__.py
│       ├─ user.py
│       ├─ patient.py
│       ├─ procedure.py
│       └─ billing_record.py
│
├─ alembic/              # Alembic migration folder
├─ alembic.ini           # Alembic configuration
├─ requirements.txt      # Python dependencies
├─ Dockerfile
├─ docker-compose.yml
└─ .env                  # Environment variables
```

---

## Purpose of Each File

| File/Folder | Purpose |
|-------------|---------|
| `main.py` | Starts FastAPI server and includes routers for endpoints. |
| `database.py` | Creates SQLAlchemy engine, session, and Base for models. Connects to PostgreSQL. |
| `models/` | Defines SQLAlchemy models for User, Patient, Procedure, BillingRecord. Each file represents a table. |
| `schemas/` | Pydantic schemas for request validation and response serialization. Prevents invalid data from entering DB. |
| `crud/` | Contains functions to Create, Read, Update, Delete data. Keeps DB logic separate from API routes. |
| `routers/` | FastAPI endpoints. Calls CRUD functions and handles HTTP requests. |
| `alembic/` | Tracks database migrations. Allows versioning of schema changes. |
| `alembic.ini` | Configures Alembic (DB connection, logging). |
| `requirements.txt` | Python dependencies: FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg2-binary, python-dotenv. |
| `Dockerfile` | Builds the API container with all dependencies. |
| `docker-compose.yml` | Orchestrates API container + PostgreSQL container, including ports and volumes. |
| `.env` | Stores sensitive info (DB URL, credentials). Loaded by database.py and Docker. |

---

## Phases of the Project

### Phase 1 – Project Setup

**Goal:** Prepare environment and Docker setup.

1. **Create Dockerfile** for FastAPI backend.

2. **Create docker-compose.yml** with two services:
   - `api` → FastAPI container
   - `db` → PostgreSQL container

3. **Add `.env`** with `DATABASE_URL`.

4. **Install Python dependencies** in `requirements.txt`.

5. **Verify Docker containers are running:**
   ```bash
   docker compose up -d
   ```

6. **Check API is accessible:** http://localhost:8000/

---

### Phase 2 – Database & Alembic Setup

**Goal:** Connect API to PostgreSQL and prepare migration system.

1. **`database.py`** → connect to DB using SQLAlchemy.

2. **Install and configure Alembic** for migrations.

3. **Initialize Alembic folder:**
   ```bash
   docker compose exec api alembic init alembic
   ```

4. **Update `alembic.ini`** with `sqlalchemy.url = ${DATABASE_URL}`

5. **Create first migration:**
   ```bash
   docker compose exec api alembic revision --autogenerate -m "create initial tables"
   docker compose exec api alembic upgrade head
   ```

**Purpose:** Keeps DB schema versioned, easy to track and update.

---

### Phase 3 – Models & Schemas

**Goal:** Define tables and validation rules.

#### Models (`models/*.py`) → SQLAlchemy ORM models

- **User:** username, email, role (admin/user)
- **Patient:** name, DOB, insurance
- **Procedure:** CPT code, description
- **BillingRecord:** links user, patient, procedure, amount, date

#### Schemas (`schemas/*.py`) → Pydantic schemas for request/response

**Why:** Separates DB logic from API validation.

---

### Phase 4 – CRUD & API Endpoints

**Goal:** Make the system functional with REST API.

#### CRUD functions (`crud/*.py`)

- **Add:** `db.add()`, `db.commit()`, `db.refresh()`
- **Read:** `db.query().filter()`, `db.query().all()`
- **Update:** modify attributes + `db.commit()`
- **Delete:** `db.delete()` + `db.commit()`

#### Routers (`routers/*.py`)

- Map endpoints like `/patients/`, `/users/`, `/billing/`
- Use FastAPI `Depends` to inject DB session.

#### Include Routers in `main.py`

```python
app.include_router(user.router)
app.include_router(patient.router)
app.include_router(procedure.router)
app.include_router(billing_record.router)
```

**Purpose:** Exposes API to front-end or clients.

---

### Phase 5 – Testing

1. **Test endpoints** using Postman or curl.
2. **Ensure DB updates correctly.**
3. **Check relationships** (BillingRecord → Patient + Procedure + User).

---

### Phase 6 – Deployment (Optional)

1. **Use Docker** to deploy locally or on cloud.
2. **Docker handles** all dependencies.
3. **Environment variables** ensure secrets are safe.

**Purpose:** Makes project portable and professional.

---

## Important Notes

**Use Docker** for professional environment → ensures consistency, avoids "works on my machine" problems.

**Alembic** for database migrations → version control for schema.

**Pydantic schemas** → validate input, prevent errors.

*CRUD module separation** → clean code, easy to maintain.

**`.env` file** → never hardcode secrets.