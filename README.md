# Automated Test Execution Scheduler

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional full-stack web application designed for QA engineers and developers to create and manage automated test scripts, schedule recurring background execution jobs (interval & cron syntax), trigger manual test runs, monitor live execution telemetry, and inspect detailed execution logs and status reports.

---

## 🚀 Features

- **JWT Authentication & Authorization**: Secure user registration, login, session persistence, password hashing via `bcrypt`, and user ownership data isolation.
- **Test Script Management**: Authenticated CRUD management of test suite definitions (`pytest` framework support, configurable timeouts, script paths).
- **Automated Pytest Execution Engine**: Safe subprocess test execution (`shell=False`), process isolation, 50KB stdout/stderr log capture, exit code mapping, and timeout enforcement.
- **Background Scheduling Engine**: Multi-mode automated scheduler powered by **APScheduler** supporting both interval (seconds) and standard 5-field cron syntax (`*/5 * * * *`). Includes pause and resume controls.
- **Execution History & Audit Trail**: Paginated and filterable execution logs searchable by test script, schedule ID, execution status (`passed`, `failed`, `timeout`, `running`), trigger type (`manual`, `scheduled`), and date range.
- **SQL-Aggregated Reporting & Analytics**: Performance statistics including total executions, status counts, success rate percentage (`(passed / completed) * 100`), and average execution duration.
- **Developer Dashboard UI**: Full React frontend featuring real-time system telemetry cards, Recharts status distribution charts, recent run duration trends, upcoming schedule previews, and a monospace output log viewer.

---

## 🏗️ Architecture

### System Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend UI                        │
│         (React 19 + TypeScript + Vite + Tailwind CSS)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST (Bearer JWT)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend API                      │
│       (Routers: Auth, Tests, Schedules, Executions)          │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐┌─────────────────────────────┐
│   APScheduler Lifecycle      ││      SQLAlchemy ORM         │
│ (Interval & Cron Background) ││(User, Test, Schedule, Exec) │
└──────────────┬───────────────┘└──────────────┬──────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐┌─────────────────────────────┐
│   Pytest Execution Engine    ││   PostgreSQL / SQLite DB    │
│  (subprocess, shell=False)   ││  (Persistence Store)        │
└──────────────────────────────┘└─────────────────────────────┘
```

### Execution & Scheduling Workflow
```
[APScheduler Trigger / Manual UI Request]
                   │
                   ▼
     [ Execution Service Layer ]
                   │
                   ▼
     [ Pytest Subprocess Runner ]
        ├── Path Security Check (Prevent Directory Traversal)
        ├── Spawn Process (shell=False)
        ├── Enforce Timeout Limit
        └── Capture & Truncate stdout / stderr Streams
                   │
                   ▼
     [ DB Persistence (Executions Table) ]
```

---

## 🛠️ Backend Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Virtual Environment tool (`venv`)

### Installation & Execution
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
5. Initialize the database schema:
   ```bash
   python ..\scripts\init_db.py
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
7. Access API documentation:
   - **Swagger OpenAPI Docs**: `http://127.0.0.1:8000/docs`
   - **ReDoc Docs**: `http://127.0.0.1:8000/redoc`
   - **Health Endpoint**: `http://127.0.0.1:8000/api/health`

---

## 💻 Frontend Setup

### Prerequisites
- Node.js 18+ and `npm`

### Installation & Execution
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install frontend packages:
   ```bash
   npm install
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173/` in your browser.
5. Compile production build:
   ```bash
   npm run build
   ```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `production`). |
| `DEBUG` | `True` | Enable debug logs & detailed error payloads. |
| `API_PREFIX` | `/api` | Base API router prefix. |
| `DATABASE_URL` | `sqlite:///./test_scheduler.db` | SQLAlchemy database URL (SQLite or PostgreSQL). |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated CORS allowed origin URLs. |
| `JWT_SECRET_KEY` | `change-this-secret-key-...` | Secret key for signing JWT access tokens. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration time in minutes (24 hours). |
| `TEST_SCRIPTS_DIR` | `test_scripts` | Base directory containing target test scripts. |

### Frontend (`frontend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api` | Base URL of the backend FastAPI service. |

---

## 🧪 Testing

Run the complete backend automated test suite (54 unit, integration, and security tests):
```bash
cd backend
pytest ../tests/test_models.py ../tests/test_auth.py ../tests/test_test_management.py ../tests/test_execution_engine.py ../tests/test_scheduling_engine.py ../tests/test_execution_reporting.py
```
*Expected Result*: **`54 passed`**.

---

## ☁️ Deployment Guide

The application is prepared for simple deployment using **Render** (or any Cloud Provider supporting Docker/Web Services and Static Sites).

### Simple Render Deployment
1. Connect your GitHub repository to [Render](https://render.com/).
2. Select **Blueprints** and point Render to [`render.yaml`](file:///c:/Users/Harsh/Desktop/Automated-Test-Execution-Scheduler/render.yaml).
3. Render automatically provisions:
   - **PostgreSQL Database**: `test-scheduler-db`
   - **FastAPI Web Service**: `test-scheduler-backend` (runs `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
   - **Static Frontend Site**: `test-scheduler-frontend` (runs `cd frontend && npm install && npm run build` publishing `frontend/dist`)
4. Set environment variables on the backend service:
   - `JWT_SECRET_KEY`: High-entropy random 32-byte secret string.
   - `ALLOWED_ORIGINS`: Production static site URL (e.g. `https://test-execution-scheduler.onrender.com`).

---

## 🔒 Security Summary

- **Password Hashing**: Passwords are hashed using `bcrypt` and never returned in API DTOs or logs.
- **JWT Authorization**: All private endpoints require `Authorization: Bearer <token>`.
- **User Ownership Isolation**: Data access is strictly isolated by user ID (`Execution -> Test -> User`).
- **Path Traversal Protection**: Script paths are sanitized and resolved strictly within `TEST_SCRIPTS_DIR`.
- **Subprocess Security**: Subprocess execution uses `shell=False` strictly without command string interpolation.
- **Environment Secrets**: Sensitive `.env` files and runtime SQLite databases are excluded via `.gitignore`.

---

## 🎯 Project Status

```
==================================================
PROJECT STATUS: COMPLETE
==================================================
```
All 10 project phases have been fully implemented, integrated, tested, and verified.
