# Automated Test Execution Scheduler

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38B2AC.svg)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-black.svg)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Render-Backend-blueviolet.svg)](https://render.com/)

A professional full-stack web application designed for QA engineers and developers to create and manage automated test scripts, schedule recurring background execution jobs (interval & cron syntax), trigger manual test runs, monitor live execution telemetry, and inspect detailed execution logs and status reports.

---

## 🚀 Features

- **Direct Dashboard Access**: Instant redirection to the main telemetry dashboard without manual authentication barriers. Includes background silent auto-authentication.
- **JWT Authentication & Ownership Isolation**: Secure user session persistence, password hashing via `bcrypt`, and user ownership data isolation across all endpoints.
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
│                (Deployed on Vercel)                         │
│         (React 19 + TypeScript + Vite + Tailwind CSS)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST (Bearer JWT)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend API                      │
│                (Deployed on Render)                         │
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

---

## 🛠️ Local Setup

### Backend Setup
1. Navigate to `backend/`:
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
4. Start FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - **Swagger Docs**: `http://127.0.0.1:8000/docs`
   - **Health Endpoint**: `http://127.0.0.1:8000/api/health`

### Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install frontend packages:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173/` in your browser.

---

## ☁️ Deployment Guide (Vercel Frontend + Render Backend)

### 1. Backend Deployment on Render
1. Connect your repository to [Render](https://render.com/).
2. Deploy using [`render.yaml`](file:///c:/Users/Harsh/Desktop/Automated-Test-Execution-Scheduler/render.yaml) or create a Python Web Service:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment Variables on Render:
   - `DATABASE_URL`: Your PostgreSQL connection string.
   - `JWT_SECRET_KEY`: Random 32-byte secret.
   - `ALLOWED_ORIGINS`: `https://*.vercel.app` (or your specific Vercel frontend URL).

### 2. Frontend Deployment on Vercel
1. Import the repository into [Vercel](https://vercel.com/).
2. Set the **Root Directory** to `frontend`.
3. Build Settings:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Environment Variables on Vercel:
   - `VITE_API_BASE_URL`: `https://<your-render-backend-name>.onrender.com/api`
5. Vercel automatically utilizes [`frontend/vercel.json`](file:///c:/Users/Harsh/Desktop/Automated-Test-Execution-Scheduler/frontend/vercel.json) for clean SPA routing.

---

## 🧪 Testing

Run the complete backend test suite (54 tests):
```bash
cd backend
pytest ../tests/test_models.py ../tests/test_auth.py ../tests/test_test_management.py ../tests/test_execution_engine.py ../tests/test_scheduling_engine.py ../tests/test_execution_reporting.py
```
*Expected Result*: **`54 passed`**.

---

## 🎯 Project Status

```
==================================================
PROJECT STATUS: COMPLETE
==================================================
```
All phases and deployment configurations for Render (Backend + PostgreSQL) and Vercel (Frontend) are complete and verified.
