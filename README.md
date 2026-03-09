# Healthcare Billing System

A comprehensive **FastAPI-based backend system** for managing healthcare billing operations, including patient records, medical procedures, billing records, and user management.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)

---

## Features

-    **RESTful API** with full CRUD operations
-    **JWT Authentication** with role-based access control
-    **PostgreSQL Database** with Alembic migrations
-    **Docker containerization** for easy deployment
-    **Interactive API Documentation** (Swagger & ReDoc)
-    **Pydantic validation** for data integrity
-    **Password hashing** with bcrypt
-    **Foreign key relationships** between entities

---

## Table of Contents

- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [Authentication](#-authentication)
- [Testing](#-testing)
- [Dashboard](#-dashboard)
- [Deployment](#-deployment)

---

## Tech Stack

- **Backend Framework:** FastAPI
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy
- **Migration Tool:** Alembic
- **Authentication:** JWT (python-jose)
- **Password Hashing:** Passlib with bcrypt
- **Containerization:** Docker & Docker Compose
- **Validation:** Pydantic
- **Dashboard:** Streamlit

---

## Project Structure

healthcare-billing/
│
├── app/
│ ├── init.py
│ ├── main.py # FastAPI application entry point
│ ├── database.py # Database configuration
│ │
│ ├── core/
│ │ ├── dependencies.py # Dependency injection
│ │ ├── security.py # JWT & password utilities
│ │ └── auth.py # Authentication middleware
│ │
│ ├── models/ # SQLAlchemy ORM models
│ │ ├── user.py
│ │ ├── patient.py
│ │ ├── procedure.py
│ │ └── billing_record.py
│ │
│ ├── schemas/ # Pydantic schemas
│ │ ├── user.py
│ │ ├── patient.py
│ │ ├── procedure.py
│ │ └── billing_record.py
│ │
│ ├── crud/ # Database operations
│ │ ├── user.py
│ │ ├── patient.py
│ │ ├── procedure.py
│ │ └── billing_record.py
│ │
│ ├── routers/ # API endpoints
│ │ ├── auth.py # Authentication routes
│ │ ├── user.py
│ │ ├── patient.py
│ │ ├── procedure.py
│ │ └── billing_record.py
│ │
│ └── scripts/
│ └── seed_data.py # Database seeding script
│
├── alembic/ # Database migrations
├── dashboard.py # Streamlit dashboard
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md


### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/healthcare-billing.git
   cd healthcare-billing