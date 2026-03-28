# Kerala Police AI Investigation Assistant (KPAIA)

A production-grade full-stack AI system for Kerala Police officers — providing real-time FIR analysis, semantic case search, MO pattern detection, legal guidance, and Malayalam FIR drafting.

---

## Table of Contents

1. [About This Project](#about-this-project)
2. [Project Build Journey — Step by Step](#project-build-journey--step-by-step)
3. [Architecture Overview](#architecture-overview)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [File Connection Map — How Every File Links Together](#file-connection-map--how-every-file-links-together)
7. [How to Run](#how-to-run)
   - [Option A — Docker (recommended)](#option-a--docker-recommended)
   - [Option B — Manual (local dev)](#option-b--manual-local-dev)
8. [Environment Variables](#environment-variables)
9. [Backend — Detailed Code Walkthrough](#backend--detailed-code-walkthrough)
10. [Frontend — Detailed Code Walkthrough](#frontend--detailed-code-walkthrough)
11. [API Reference](#api-reference)
12. [How the AI Pipeline Works](#how-the-ai-pipeline-works)
13. [Data Flow — Request Lifecycle](#data-flow--request-lifecycle)
14. [Design Decisions & Why](#design-decisions--why)
15. [First-Time Usage](#first-time-usage)

---

## About This Project

**Kerala Police AI Investigation Assistant (KPAIA)** is a full-stack AI web application designed to assist Kerala Police officers in their day-to-day investigation workflows. The system combines **Natural Language Processing (NLP)**, **vector similarity search**, and a **curated Indian legal knowledge base** to automate tasks that traditionally require hours of manual effort.

### What Problems Does It Solve?

| Problem | How KPAIA Solves It |
|---|---|
| Officers manually read through FIRs to identify relevant IPC sections | AI automatically classifies IPC/CrPC/BNS sections with confidence scores |
| No easy way to find similar past cases across districts | Semantic vector search finds similar FIRs using ChromaDB embeddings |
| Identifying crime patterns (like serial chain-snatching) takes weeks | MO pattern engine detects modus operandi clusters in real-time |
| Legal knowledge is scattered across books and manuals | Built-in knowledge base with IPC, CrPC, BNS, POCSO, MVA, and landmark judgments |
| FIRs need to be drafted in Malayalam for Kerala courts | Bhashini API integration translates English FIRs to Malayalam instantly |
| No centralized dashboard for crime intelligence | Live dashboard with risk breakdown, district stats, and pattern alerts |

### Core Features

1. **FIR Analysis** — Upload a FIR (PDF or text) → AI extracts entities (complainant, accused, location, weapon), suggests IPC sections, assigns risk level, and detects MO patterns
2. **Case Intelligence** — Browse all indexed FIRs with filters, find semantically similar cases using vector search
3. **MO Pattern Alerts** — Detect crime clusters like OTP fraud, chain snatching, house breaking across districts
4. **Legal Assistant** — Search IPC, CrPC, BNS, POCSO, Motor Vehicles Act, and landmark Supreme Court judgments
5. **Malayalam FIR Drafting** — Convert English FIR content to formatted Malayalam using Bhashini (Government of India NLP API)
6. **Officer Authentication** — JWT-based login with role hierarchy (Constable → Sub Inspector → Inspector → DSP → SP → Admin)

---

## Project Build Journey — Step by Step

This section explains the **logical order** in which the project was designed and built, and **why** each step was taken.

### Step 1: Define the Problem & Plan the Architecture

**Goal:** Understand what Kerala Police officers need most — fast FIR analysis, legal lookup, and case similarity search.

**Decision:** Use a full-stack architecture with:
- **React frontend** for the officer-facing UI
- **FastAPI backend** for async API performance
- **PostgreSQL** for relational data (officers, FIRs, cases)
- **ChromaDB** for vector similarity search
- **Celery + Redis** for background processing of heavy ML tasks

### Step 2: Set Up the Backend Foundation

**Files created:**
- `backend/main.py` — FastAPI app with lifespan hook for startup tasks
- `backend/app/core/config.py` — Centralized settings using `pydantic-settings` (reads `.env`)
- `backend/app/core/database.py` — Async SQLAlchemy engine with PostgreSQL (`asyncpg` driver)
- `backend/app/core/security.py` — JWT token creation/validation + bcrypt password hashing

**Why this order?** Config must come first because every other module imports `settings`. Database comes next because models depend on the `Base` class. Security comes third because the auth API depends on password hashing and JWT functions.

### Step 3: Define the Database Models

**Files created:**
- `backend/app/models/officer.py` — Officers table with badge number, station, district, role hierarchy, and bcrypt password hash
- `backend/app/models/fir.py` — FIRs table with raw text, extracted entities (JSON), IPC sections (JSON), risk level, MO pattern, embedding ID, and status tracking
- `backend/app/models/case.py` — Cases table (one-to-one with FIR) with investigation status, court tracking, and officer assignment

**Why?** The data model must be defined before any API or service code. The FIR model is the most complex — it stores both raw data and all AI-computed fields (entities, IPC sections, risk, MO pattern, embedding reference).

**Key relationship:** `Officer` → (has many) → `FIR` → (has one) → `Case`

### Step 4: Define Request/Response Schemas

**File created:**
- `backend/app/schemas/schemas.py` — All Pydantic models for API validation

**Contains:** `LoginRequest`, `TokenResponse`, `OfficerCreate`, `OfficerOut`, `FIRCreate`, `FIROut`, `FIRListItem`, `AnalysisRequest`, `AnalysisResponse`, `SimilarFIR`, `LegalSearchRequest`, `LegalSearchResponse`, `TranslationRequest`, `TranslationResponse`, `DashboardStats`, `MOPattern`

**Why separate from models?** SQLAlchemy models define the database schema. Pydantic schemas define the API contract (what the frontend sends/receives). They're intentionally different — for example, `OfficerOut` excludes `hashed_password`.

### Step 5: Build the AI/ML Services (The Intelligence Core)

**Files created (in dependency order):**

1. **`backend/app/services/nlp_service.py`** (445 lines) — The heart of the system
   - Hand-curated **IPC Knowledge Base** with 24 sections (IPC 302–509, IT Act 66–67, NDPS Act 20–22)
   - Each section has keywords, title, description, punishment, bailable status
   - `extract_entities()` — spaCy NER + regex fallback for complainant, accused, location, weapon, vehicle, property
   - `suggest_ipc_sections()` — Keyword scoring engine with confidence calculation
   - `detect_mo_pattern()` — Rule-based pattern detection (ATM skimming, OTP fraud, chain snatching, etc.)
   - `generate_summary()` — Structured AI summary from entities + IPC sections
   - `generate_next_steps()` — Investigation steps tailored to crime type

2. **`backend/app/services/embedding_service.py`** — Sentence-transformer encoder
   - Model: `paraphrase-multilingual-MiniLM-L12-v2` (supports English + Malayalam)
   - Encodes FIR text into 384-dimensional normalized vectors
   - Singleton pattern — model loads once at startup, stays in memory

3. **`backend/app/services/chroma_service.py`** — ChromaDB vector store client
   - Uses `fir_embeddings` collection with cosine distance
   - `upsert_fir()` stores vector + metadata (case number, district, risk)
   - `search_similar()` finds top-K nearest FIRs by cosine similarity
   - Graceful fallback if ChromaDB is unreachable

4. **`backend/app/services/bhashini_service.py`** — Bhashini/IndicTrans2 translation
   - Calls the Government of India Bhashini Dhruva API for English → Malayalam
   - Falls back to realistic Malayalam mock if API key not configured
   - Mock includes proper Malayalam FIR structure with key term translations

5. **`backend/app/services/training_service.py`** — FIR ingestion pipeline orchestrator
   - `ingest_fir()` chains all services: NLP → Embedding → ChromaDB → DB update
   - Also includes `extract_text_from_pdf()` using pdfplumber

**Why this order?** Each service is independent and stateless. The training service depends on all three AI services (NLP, embedding, ChromaDB), so it must come last.

### Step 6: Build the API Endpoints

**Files created:**
- `backend/app/api/auth.py` — Login, register, seed-demo, get-me
- `backend/app/api/firs.py` — Upload, list, get, train (triggers ingestion pipeline)
- `backend/app/api/analysis.py` — Real-time FIR analysis + semantic similarity search
- `backend/app/api/legal.py` — Legal knowledge base search (IPC, CrPC, BNS, POCSO, MVA, judgments)
- `backend/app/api/patterns.py` — MO pattern detection across all FIRs
- `backend/app/api/dashboard.py` — Live statistics (7 async DB queries)
- `backend/app/api/bhashini.py` — Translation proxy endpoint

**All routes** require JWT authentication (`Depends(get_current_officer)`) except login, seed-demo, and health check.

### Step 7: Set Up the Celery Background Worker

**File created:**
- `backend/app/tasks/train_pipeline.py` — Celery task wrapper

**Why Celery?** FIR ingestion involves heavy ML operations (spaCy NER + sentence-transformer encoding + ChromaDB upsert). For single FIRs, FastAPI's `BackgroundTasks` works fine. But for bulk uploads or re-training, Celery + Redis provides a proper distributed task queue with retries and monitoring.

### Step 8: Build the React Frontend

**Files created (in dependency order):**

1. **`frontend/src/main.jsx`** — React 18 root with `react-hot-toast` provider
2. **`frontend/src/styles/index.css`** — Tailwind CSS config + custom Kerala Police theme (navy/gold)
3. **`frontend/src/api/index.js`** — Axios client with JWT interceptor and all API helper functions
4. **`frontend/src/components/AuthContext.jsx`** — React Context for officer login state (persists in localStorage)
5. **`frontend/src/components/Layout.jsx`** — Sidebar navigation + topbar + user card
6. **`frontend/src/App.jsx`** — BrowserRouter with route definitions and `PrivateRoute` guard
7. **Pages (each is a self-contained feature):**
   - `Login.jsx` — Officer login form
   - `Dashboard.jsx` — Stats + charts + MO alerts
   - `FIRAnalysis.jsx` — FIR upload/paste → AI analysis results
   - `CaseIntelligence.jsx` — Browse and search indexed FIRs
   - `MOPatterns.jsx` — Crime pattern alerts dashboard
   - `LegalAssistant.jsx` — Chat-style legal query interface
   - `MalayalamFIR.jsx` — English → Malayalam FIR generator
   - `RequestAccess.jsx` — New officer registration request

### Step 9: Containerize Everything with Docker

**Files created:**
- `backend/Dockerfile` — Python 3.11-slim image with pip requirements
- `frontend/Dockerfile` — Multi-stage build: Node 20 (build) → Nginx (serve), with API proxy config
- `docker-compose.yml` — Orchestrates 6 services: PostgreSQL, Redis, ChromaDB, Backend, Celery Worker, Frontend

### Step 10: Configuration & Documentation

**Files created:**
- `.env.example` / `.env` — All environment variables
- `backend/setup.ps1` — PowerShell setup script for Windows local dev
- `backend/start.ps1` — PowerShell script to start the backend
- `backend/scripts/upload_firs.py` — Bulk FIR upload utility
- `backend/tests/test_auth.py` — Pytest auth endpoint tests
- `backend/tests/sample_fir.txt` — Realistic FIR text for testing
- `README.md` — This file

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│           React + Vite + Tailwind Frontend       │
│      Officer Login · Dashboard · FIR Analysis    │
│   Case Intelligence · Legal Chat · Malayalam FIR │
└─────────────────────┬────────────────────────────┘
                      │  REST API (JSON over HTTP)
                      │  Vite dev proxy → localhost:8000
┌─────────────────────▼────────────────────────────┐
│               FastAPI Backend (Python)           │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ FIR API  │  │ Analysis │  │  Legal / MO    │  │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │             │                 │          │
│  ┌────▼──────┐ ┌────▼───────┐ ┌──────▼────────┐  │
│  │PostgreSQL │ │  ChromaDB  │ │ Bhashini API  │  │
│  │(Case DB)  │ │(FIR vectors│ │  (Malayalam)  │  │
│  └───────────┘ └────────────┘ └───────────────┘  │
│                      │                           │
│               ┌──────▼────────┐                  │
│               │  Celery+Redis │ (async training) │
│               └───────────────┘                  │
└──────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind CSS | Fast dev server, component model, utility CSS |
| Backend | FastAPI (Python 3.11+) | Async, auto-docs, high performance |
| NLP / NER | spaCy `en_core_web_sm` | Named Entity Recognition from FIR text |
| Embeddings | `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) | Supports English + Malayalam text in 384-dim vectors |
| IPC Classification | Custom rule/keyword engine (in `nlp_service.py`) | 24 IPC/CrPC/IT Act sections with confidence scoring |
| Vector DB | ChromaDB | Semantic similarity search across all indexed FIRs |
| Database | PostgreSQL via SQLAlchemy (async) | Persistent FIR/case/officer storage |
| Migrations | Alembic | Schema versioning |
| Malayalam NLP | Bhashini API (IndicTrans2) | Government of India NLP translation pipeline |
| Background Jobs | Celery + Redis | Async FIR ingestion/training pipeline |
| Auth | JWT (python-jose) + bcrypt | Stateless officer login |
| PDF extraction | pdfplumber | Extracts text from uploaded FIR PDFs |
| Containerisation | Docker + docker-compose | One-command startup of all 6 services |

---

## Project Structure

```
kerala-police-ai/
├── docker-compose.yml          ← Spins up all 6 services
├── .env.example                ← Copy to .env and fill in secrets
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 ← FastAPI app entry point
│   ├── setup.ps1               ← Windows local dev setup script
│   ├── start.ps1               ← Windows local dev start script
│   │
│   └── app/
│       ├── core/
│       │   ├── config.py       ← Reads all settings from .env
│       │   ├── database.py     ← Async SQLAlchemy engine + session
│       │   └── security.py     ← JWT creation, bcrypt, auth dependency
│       │
│       ├── models/             ← SQLAlchemy ORM models (DB tables)
│       │   ├── officer.py      ← Officers table (badge, station, role)
│       │   ├── fir.py          ← FIRs table (text, entities, IPC, risk)
│       │   └── case.py         ← Cases table (status, court, notes)
│       │
│       ├── schemas/
│       │   └── schemas.py      ← All Pydantic request/response models
│       │
│       ├── services/           ← Core AI/ML logic — all stateless
│       │   ├── nlp_service.py          ← spaCy NER + IPC rule engine
│       │   ├── embedding_service.py    ← sentence-transformer encoder
│       │   ├── chroma_service.py       ← ChromaDB vector store client
│       │   ├── bhashini_service.py     ← Bhashini/IndicTrans2 API
│       │   └── training_service.py     ← Full FIR ingestion pipeline
│       │
│       ├── api/                ← FastAPI route handlers
│       │   ├── auth.py         ← POST /api/auth/login, GET /me
│       │   ├── firs.py         ← FIR upload, list, get, train
│       │   ├── analysis.py     ← NLP analysis + similarity search
│       │   ├── legal.py        ← IPC/CrPC/BNS/POCSO/judgment search
│       │   ├── patterns.py     ← MO pattern clustering
│       │   ├── dashboard.py    ← Live stats
│       │   └── bhashini.py     ← Translation proxy
│       │
│       └── tasks/
│           └── train_pipeline.py   ← Celery async task wrapper
│
│   ├── scripts/
│   │   └── upload_firs.py      ← Bulk FIR upload utility
│   │
│   ├── tests/
│   │   ├── test_auth.py        ← Pytest auth endpoint tests
│   │   └── sample_fir.txt      ← Realistic FIR for testing
│   │
│   └── fir_data/
│       └── README.md           ← Instructions for FIR data files
│
└── frontend/
    ├── Dockerfile              ← Multi-stage: Node build → Nginx serve
    ├── package.json
    ├── vite.config.js          ← Dev server + proxy to :8000
    ├── tailwind.config.js      ← Kerala Police navy/gold theme
    ├── postcss.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx            ← React 18 root + toast provider
        ├── App.jsx             ← BrowserRouter + route definitions
        ├── styles/index.css    ← Tailwind + global dark theme
        │
        ├── api/index.js        ← Axios client — all API helpers + JWT interceptor
        │
        ├── components/
        │   ├── AuthContext.jsx  ← React context for officer login state
        │   └── Layout.jsx      ← Sidebar + topbar wrapper
        │
        └── pages/
            ├── Login.jsx           ← Officer login (badge + password)
            ├── RequestAccess.jsx   ← New officer registration request
            ├── Dashboard.jsx       ← Live stats, charts, MO alerts
            ├── FIRAnalysis.jsx     ← Upload/paste FIR → AI analysis
            ├── CaseIntelligence.jsx← Browse indexed FIRs + similarity
            ├── MOPatterns.jsx      ← Crime pattern alerts + detail
            ├── LegalAssistant.jsx  ← Chat UI for IPC/CrPC queries
            └── MalayalamFIR.jsx    ← English form → Malayalam FIR
```

---

## File Connection Map — How Every File Links Together

This section shows exactly **how each file imports from and depends on other files**. Understanding these connections is essential for modifying the codebase.

### Backend File Dependencies

```
.env
  └── read by → config.py (via pydantic-settings)

config.py (settings singleton)
  └── imported by → database.py, security.py, embedding_service.py,
                     chroma_service.py, bhashini_service.py, train_pipeline.py

database.py (Base class + get_db dependency + engine)
  └── imported by → ALL models (officer.py, fir.py, case.py)
  └── imported by → ALL api endpoints (via get_db dependency)
  └── imported by → training_service.py, train_pipeline.py

security.py (JWT + bcrypt + get_current_officer dependency)
  └── imported by → ALL api endpoints (via get_current_officer)
  └── imports ← config.py (for SECRET_KEY, ALGORITHM)
  └── imports ← database.py (for get_db)
  └── imports ← models/officer.py (to look up officer from JWT)

models/officer.py (Officer ORM model)
  └── imports ← database.py (Base)
  └── imported by → security.py, auth.py, all API files (via get_current_officer)
  └── has relationship → fir.py (Officer.firs ↔ FIR.officer)

models/fir.py (FIR ORM model)
  └── imports ← database.py (Base)
  └── imported by → firs.py, analysis.py, dashboard.py, patterns.py, training_service.py
  └── has relationship → officer.py (FIR.officer ↔ Officer.firs)
  └── has relationship → case.py (FIR.case ↔ Case.fir)

models/case.py (Case ORM model)
  └── imports ← database.py (Base)
  └── imported by → dashboard.py
  └── has relationship → fir.py (Case.fir ↔ FIR.case)

schemas/schemas.py (all Pydantic models)
  └── imports ← models/officer.py (OfficerRole enum)
  └── imported by → ALL api endpoints

services/nlp_service.py → STANDALONE (no internal imports)
  └── imported by → training_service.py, analysis.py
  └── exports → IPC_KNOWLEDGE_BASE (also imported by legal.py)

services/embedding_service.py
  └── imports ← config.py (model name, cache dir)
  └── imported by → training_service.py, analysis.py

services/chroma_service.py
  └── imports ← config.py (host, port)
  └── imported by → training_service.py, analysis.py, dashboard.py

services/bhashini_service.py
  └── imports ← config.py (API key, user ID)
  └── imported by → api/bhashini.py

services/training_service.py (THE ORCHESTRATOR)
  └── imports ← nlp_service.py + embedding_service.py + chroma_service.py
  └── imports ← models/fir.py
  └── imported by → api/firs.py (BackgroundTask), tasks/train_pipeline.py (Celery)

tasks/train_pipeline.py
  └── imports ← config.py (Redis URL), database.py, training_service.py
  └── used by → Celery worker process (docker-compose command)

main.py (APP ENTRY POINT)
  └── imports ← ALL api routers (auth, firs, analysis, legal, patterns, dashboard, bhashini)
  └── imports ← config.py, database.py
  └── imports ← embedding_service.py (warmup), chroma_service.py (init)
  └── registers all routes under /api/... prefixes
```

### Frontend File Dependencies

```
main.jsx (ENTRY POINT)
  └── imports ← App.jsx, styles/index.css
  └── renders App inside React.StrictMode + Toaster

App.jsx (ROUTER)
  └── imports ← AuthContext.jsx (AuthProvider + useAuth)
  └── imports ← Layout.jsx
  └── imports ← ALL page components
  └── defines PrivateRoute (checks officer state → redirects to /login if null)
  └── defines AppRoutes (maps URL paths to page components)

api/index.js (AXIOS CLIENT)
  └── creates Axios instance with baseURL '/api'
  └── request interceptor: attaches JWT from localStorage
  └── response interceptor: on 401, clears auth and redirects to /login
  └── exports: authAPI, firsAPI, analysisAPI, legalAPI, patternsAPI,
               dashboardAPI, bhashiniAPI
  └── imported by → AuthContext.jsx, Layout.jsx, ALL page components

components/AuthContext.jsx
  └── imports ← api/index.js (authAPI)
  └── provides: { officer, login, logout, loading } via React Context
  └── imported by → App.jsx (AuthProvider), Login.jsx (useAuth)
  └── persists officer in localStorage for page refresh survival

components/Layout.jsx
  └── imports ← api/index.js (authAPI.me)
  └── renders sidebar navigation, topbar, user card, logout
  └── wraps ALL authenticated pages (passed as children prop from App.jsx)

pages/Login.jsx → uses authAPI.login() via AuthContext.login()
pages/Dashboard.jsx → uses dashboardAPI.getStats() + patternsAPI.getMOAlerts()
pages/FIRAnalysis.jsx → uses analysisAPI.analyzeFIR() + firsAPI.upload()
pages/CaseIntelligence.jsx → uses firsAPI.list() + firsAPI.get() + analysisAPI.getSimilar()
pages/MOPatterns.jsx → uses patternsAPI.getMOAlerts()
pages/LegalAssistant.jsx → uses legalAPI.search()
pages/MalayalamFIR.jsx → uses bhashiniAPI.translate()
pages/RequestAccess.jsx → standalone form (no API call yet)
```

### Cross-Stack Connection: Frontend ↔ Backend

```
Frontend (port 5173)          Backend (port 8000)
─────────────────────         ─────────────────────
api/index.js                  
  baseURL: '/api'    ──────→  Vite proxy OR Nginx proxy
                              ──────→ main.py routes:
authAPI.login()      ──────→  POST /api/auth/login     → auth.py
authAPI.me()         ──────→  GET  /api/auth/me         → auth.py
authAPI.seedDemo()   ──────→  POST /api/auth/seed-demo  → auth.py
firsAPI.upload()     ──────→  POST /api/firs/upload     → firs.py
firsAPI.list()       ──────→  GET  /api/firs/           → firs.py
firsAPI.get(id)      ──────→  GET  /api/firs/{id}       → firs.py
firsAPI.train(id)    ──────→  POST /api/firs/{id}/train → firs.py
analysisAPI.analyzeFIR() ──→  POST /api/analysis/analyze-fir → analysis.py
analysisAPI.getSimilar() ──→  GET  /api/analysis/similar/{id} → analysis.py
legalAPI.search()    ──────→  POST /api/legal/search    → legal.py
patternsAPI.getMOAlerts()──→  GET  /api/patterns/mo-alerts → patterns.py
dashboardAPI.getStats()  ──→  GET  /api/dashboard/stats → dashboard.py
dashboardAPI.getChromaStats()→GET /api/dashboard/chroma-stats → dashboard.py
bhashiniAPI.translate()  ──→  POST /api/bhashini/translate → bhashini.py
```

### Docker Service Dependencies

```
docker-compose.yml orchestrates:

postgres (port 5432)     ← no dependencies
redis (port 6379)        ← no dependencies
chromadb (port 8001)     ← no dependencies
backend (port 8000)      ← depends on: postgres (healthy), redis (healthy), chromadb
celery_worker            ← depends on: postgres, redis, chromadb
frontend (port 5173→80)  ← depends on: backend

Frontend Nginx config proxies /api/* → http://backend:8000
Backend connects to postgres, redis, chromadb via Docker service names
```

---

## How to Run

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Option A)
- **OR** Python 3.11+, Node.js 18+, PostgreSQL 15, Redis 7, ChromaDB (for Option B)

---

### Option A — Docker (recommended)

This starts everything: FastAPI, PostgreSQL, ChromaDB, Redis, Celery worker, and the compiled frontend.

**Step 1 — Copy and configure env:**
```bash
cd kerala-police-ai
cp .env.example .env
# Edit .env if you have Bhashini or Google Maps API keys (optional)
```

**Step 2 — Build and start all services:**
```bash
docker-compose up --build
```

> First run downloads the `paraphrase-multilingual-MiniLM-L12-v2` model (~90 MB) and the spaCy `en_core_web_sm` model. This is cached in a Docker volume so subsequent starts are fast.

**Step 3 — Seed demo officer:**
```bash
curl -X POST http://localhost:8000/api/auth/seed-demo
```
Or just visit the app and click **"Seed Demo Credentials"** on the login page.

**Step 4 — Open the app:**
- Frontend: http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/api/docs

Login with: **Badge: `KP001`  Password: `test1234`**

---

### Option B — Manual (local dev)

#### Backend

```bash
cd kerala-police-ai/backend

# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download the spaCy English model
python -m spacy download en_core_web_sm

# 4. Set up environment variables
cp ../.env.example ../.env
# Edit .env — set DATABASE_URL, CHROMA_HOST, REDIS_URL etc.

# 5. Start PostgreSQL, ChromaDB and Redis (Docker is easiest even for local dev):
docker run -d -p 5432:5432 -e POSTGRES_USER=kpai -e POSTGRES_PASSWORD=kpai_secret -e POSTGRES_DB=kpai_db postgres:15-alpine
docker run -d -p 8001:8000 chromadb/chroma:latest
docker run -d -p 6379:6379 redis:7-alpine

# 6. Run the FastAPI server
uvicorn main:app --reload --port 8000
```

> The database tables are created automatically on startup — no need to run Alembic migrations manually for first-time use.

#### Frontend

```bash
cd kerala-police-ai/frontend

# Install dependencies
npm install

# Start dev server (proxies /api to localhost:8000)
npm run dev
```

Open http://localhost:5173

#### Backend Tests (optional)

```bash
cd backend
pip install aiosqlite pytest-anyio
pytest tests/ -v
```

---

## Environment Variables

All settings live in `.env` (copy from `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key (change in production!) |
| `CHROMA_HOST` | ✅ | ChromaDB host (default: `localhost`) |
| `CHROMA_PORT` | ✅ | ChromaDB port (default: `8001` local, `8000` in Docker) |
| `REDIS_URL` | ✅ | Redis URL for Celery task queue |
| `BHASHINI_API_KEY` | ⬜ | Bhashini API key — if blank, uses realistic Malayalam mock |
| `BHASHINI_USER_ID` | ⬜ | Bhashini User ID |
| `GOOGLE_MAPS_API_KEY` | ⬜ | For crime geolocation features (optional) |
| `EMBEDDING_MODEL` | ⬜ | Sentence transformer model name (default: `paraphrase-multilingual-MiniLM-L12-v2`) |

> **Bhashini API:** Register at https://bhashini.gov.in/ulca/user/register to get a free API key for real Malayalam translation.

---

## Backend — Detailed Code Walkthrough

### `main.py` — FastAPI Entry Point

The `lifespan` context manager runs on startup:
1. Creates all DB tables from ORM models (`Base.metadata.create_all`)
2. Loads and warms up the sentence-transformer embedding model
3. Connects to ChromaDB and creates/gets the `fir_embeddings` collection

All 7 routers are registered with `/api/...` prefixes. CORS is configured to allow the React dev server (`localhost:5173`).

---

### `app/core/`

#### `config.py`
Uses **pydantic-settings** `BaseSettings` to read every config value from `.env`. All app code imports `settings` — no raw `os.getenv()` calls anywhere. This makes the app testable (override settings per test).

#### `database.py`
- Creates an **async SQLAlchemy engine** using `asyncpg` driver
- `AsyncSessionLocal` is a session factory used across all API handlers
- `get_db()` is a FastAPI dependency that yields a session per request, commits on success, rolls back on error

#### `security.py`
- `get_password_hash()` / `verify_password()` — bcrypt hashing
- `create_access_token()` — encodes officer badge number + role into a signed JWT
- `get_current_officer()` — FastAPI dependency that decodes the JWT from the `Authorization: Bearer` header and fetches the officer from DB

---

### `app/models/`

All three models inherit from the shared `Base` class.

#### `officer.py`
Represents a police officer. Key fields:
- `badge_number` — unique login identifier (e.g., `KP001`)
- `station`, `district` — posting location
- `role` — enum: `constable`, `sub_inspector`, `inspector`, `dsp`, `sp`, `admin`
- `hashed_password` — bcrypt hash, never stored in plain text

#### `fir.py`
The core model. Key fields:
- `raw_text` — full FIR text (English or Malayalam)
- `extracted_entities` — JSON: `{"complainant": ..., "accused": [...], "weapon": ..., ...}`
- `ipc_sections` — JSON list: `[{"section": "379", "title": "Theft", "confidence": 0.85, ...}]`
- `risk_level` — enum: `low`, `medium`, `high`, `critical`
- `mo_pattern` — detected modus operandi string (e.g., `"Bike-Borne Chain Snatching"`)
- `status` — `pending` → `indexed` (once ChromaDB vector is stored)
- `embedding_id` — the ChromaDB document ID (same as `fir.id` as string)

#### `case.py`
One-to-one with FIR. Tracks investigation progress: `status`, `court_name`, `court_case_number`, `next_hearing_date`, `notes`.

---

### `app/services/`

This is where all the intelligence lives.

#### `nlp_service.py` — The Intelligence Core

**IPC Knowledge Base:** A hand-curated list of 24 IPC/IT Act/NDPS sections, each with:
- `keywords` — list of triggering words/phrases
- `title`, `description`, `punishment`, `bailable`

**`extract_entities(text)`:**
1. Runs spaCy NER to find `PERSON`, `GPE`/`LOC`, `DATE`/`TIME` entities
2. Falls back to regex patterns if spaCy isn't available
3. Detects weapons, vehicles (licence plate regex), and stolen property via pattern matching

**`suggest_ipc_sections(text, entities)`:**
- For each IPC section in the knowledge base, counts how many keywords appear in the FIR text
- Assigns a confidence score = `0.4 + (keyword_hits / total_keywords) * 0.55`
- Returns top 5 matches sorted by confidence

**`detect_mo_pattern(text, sections)`:**
- Checks for specific phrase patterns (e.g., `"atm"` + `"card cloning"` → `"ATM/Card Skimming"`)
- Returns `None` if no pattern matches

**`generate_next_steps(sections, risk_level)`:**
- Returns a priority-ordered list of investigation steps based on which IPC sections were matched (different steps for murder vs. theft vs. cybercrime vs. sexual offences)

---

#### `embedding_service.py` — Multilingual Vector Encoder

**Model:** `paraphrase-multilingual-MiniLM-L12-v2`
- 50+ language support including Malayalam
- Outputs 384-dimension normalized float vectors
- Downloaded automatically on first run, cached in `.model_cache/`

**`embed(text)`:** Truncates text to 5,000 chars, runs through the model with `normalize_embeddings=True` (so cosine similarity = dot product, which is faster).

The service is a **singleton** — the model loads once at startup (via `warmup()` in `main.py`) and stays in memory.

---

#### `chroma_service.py` — Vector Store

Connects to ChromaDB via HTTP client. Uses the `fir_embeddings` collection with `hnsw:space = cosine` (cosine distance metric).

**`upsert_fir(fir_id, vector, metadata)`:** Stores the embedding alongside metadata (case number, district, crime category, risk level) so search results can be understood without extra DB lookups.

**`search_similar(vector, k=5)`:**
- Queries ChromaDB for `k` nearest vectors
- Converts distance to similarity: `similarity = 1.0 - distance`
- Returns `[{id, similarity, metadata}]`

**Graceful fallback:** If ChromaDB is unreachable, `is_available` returns `False` and all callers skip similarity search silently.

---

#### `bhashini_service.py` — Malayalam Translation

Calls the **Bhashini Dhruva API** with the IndicTrans2 pipeline for English → Malayalam translation.

**If `BHASHINI_API_KEY` is not set:** Returns a realistic Malayalam FIR mock — the output includes a properly structured FIR header in Malayalam script with key term translations (e.g., "theft" → `"മോഷണം(theft)"`).

---

#### `training_service.py` — FIR Ingestion Pipeline

`ingest_fir(fir_id, db)` orchestrates the full pipeline in order:
1. Load FIR from DB
2. Run `nlp_service.extract_entities()` → JSON
3. Run `nlp_service.suggest_ipc_sections()` → list
4. Compute risk level, crime category, MO pattern
5. Generate AI summary text
6. Run `embedding_service.embed()` → 384-dim vector
7. `chroma_service.upsert_fir()` → stored in vector index
8. Update FIR record: status → `indexed`, all fields populated

This runs **inline** (as a FastAPI `BackgroundTask`) on upload, and can also be triggered via Celery for heavy loads.

---

### `app/api/`

All routes use `Depends(get_current_officer)` — a valid JWT is required for every endpoint except `/api/auth/login` and `/api/auth/seed-demo`.

#### `auth.py`
- `POST /api/auth/login` — looks up officer by badge number, verifies bcrypt password, returns JWT + officer object
- `POST /api/auth/seed-demo` — creates two test officers (`KP001`, `KP002`) with password `test1234`. Disabled in production.
- `GET /api/auth/me` — returns the current officer from JWT

#### `firs.py`
- `POST /api/firs/upload` — accepts either a file upload (PDF/TXT) or raw text via form. Extracts text from PDF using `pdfplumber`. Creates FIR in DB and queues the ingestion pipeline as a background task.
- `GET /api/firs/` — lists FIRs with optional filters: `district`, `risk_level`, `status`
- `POST /api/firs/{id}/train` — re-runs the ingestion pipeline on an existing FIR

#### `analysis.py`
- `POST /api/analysis/analyze-fir` — the main AI endpoint. Takes raw FIR text, runs the full NLP pipeline (entities → IPC → risk → MO → embedding → ChromaDB search), returns a structured `AnalysisResponse`
- `GET /api/analysis/similar/{fir_id}` — finds semantically similar FIRs for an already-indexed FIR

#### `legal.py`
Contains a large in-file knowledge base with:
- 24 IPC sections (from `nlp_service.py`)
- 7 CrPC provisions (Sec 41, 57, 154, 161, 167, 173, 436A)
- 3 landmark judgments (D.K. Basu, Lalita Kumari, Arnesh Kumar)
- 6 Motor Vehicles Act sections (drunk driving, dangerous driving, hit-and-run, etc.)
- 5 BNS/BNSS sections (new criminal laws effective 1 July 2024)
- 3 POCSO sections (child sexual abuse, mandatory reporting)
- 2 Domestic Violence provisions (DV Act 2005, IPC 498A)

`search_legal_kb(query)` scores each item by keyword matches + title match and returns the top 5 with a structured answer + citation.

#### `patterns.py`
Defines 6 known MO cluster patterns (OTP fraud, chain snatching, house breaking, romance fraud, ATM skimming, narcotics network). On each request, scans all FIRs in the DB for keyword matches and returns occurrence counts per district. Results are sorted by risk level.

#### `dashboard.py`
Runs 7 async DB queries (total FIRs, indexed count, case statuses, risk breakdown, district breakdown, today's count) and returns them as a single `DashboardStats` object.

---

## Frontend — Detailed Code Walkthrough

### `src/api/index.js` — Axios Client

Single Axios instance with:
- `baseURL: '/api'` — Vite's dev proxy forwards to `localhost:8000`
- **Request interceptor:** reads `kpai_token` from localStorage, attaches `Authorization: Bearer <token>`
- **Response interceptor:** on 401, clears storage and redirects to `/login`
- Exports typed helper objects: `authAPI`, `firsAPI`, `analysisAPI`, `legalAPI`, `patternsAPI`, `dashboardAPI`, `bhashiniAPI`

### `src/components/AuthContext.jsx`

React Context that holds the logged-in officer object. `login()` calls the API, stores the JWT + officer in `localStorage`, and updates state. `logout()` clears both. The context persists the officer across page refreshes by reading from localStorage on init.

### `src/components/Layout.jsx`

The persistent chrome around all pages:
- **Sidebar** with navigation menu (Dashboard, FIR Analysis, Case Intelligence, MO Patterns, Legal Assistant, Malayalam FIR)
- **Active route highlighting** via `useLocation()`
- **Officer card** at the bottom with initials avatar and logout button
- **Topbar** with current page title, search bar, and notification bell

### Page Components

| Page | What it does |
|---|---|
| `Login.jsx` | Badge/password form → `authAPI.login()`. Shows Kerala Police branding with illustration panel. |
| `RequestAccess.jsx` | New officer registration form for access requests. |
| `Dashboard.jsx` | On mount fetches `dashboardAPI.getStats()` and `patternsAPI.getMOAlerts()`. Displays stat cards (total FIRs, high risk, indexed, open cases), district breakdown, and ChromaDB vector count. |
| `FIRAnalysis.jsx` | Text input or file upload. Calls `analysisAPI.analyzeFIR()`. Displays extracted entities, IPC sections with confidence bars, similar cases from ChromaDB, risk level badge, MO pattern, AI summary, and next investigation steps. |
| `CaseIntelligence.jsx` | Left panel: filterable FIR list from `firsAPI.list()`. Right panel: FIR detail view. Clicking a case fetches `analysisAPI.getSimilar()` for similar cases. "Re-train" button triggers `firsAPI.train()`. |
| `MOPatterns.jsx` | Fetches all patterns on mount. Displays pattern cards colored by risk level (critical=red, high=orange, medium=yellow). Shows description, affected districts, linked FIR IDs, and recommended police action. |
| `LegalAssistant.jsx` | Chat-style UI. Sends query via `legalAPI.search()`. Renders legal answers with citations. Sidebar with quick-query shortcuts for common legal queries. |
| `MalayalamFIR.jsx` | Structured FIR form (case number, station, complainant details). On submit, assembles English text and calls `bhashiniAPI.translate()`. Renders Malayalam output with copy/print options. |

---

## API Reference

Full interactive docs at **http://localhost:8000/api/docs** (Swagger UI).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | ❌ | Officer login → JWT |
| `POST` | `/api/auth/seed-demo` | ❌ | Seed demo officers (dev only) |
| `POST` | `/api/auth/register` | ❌ | Register new officer |
| `GET` | `/api/auth/me` | ✅ | Current officer info |
| `POST` | `/api/firs/upload` | ✅ | Upload FIR (PDF/text form) |
| `GET` | `/api/firs/` | ✅ | List all FIRs (with filters) |
| `GET` | `/api/firs/{id}` | ✅ | Get single FIR |
| `POST` | `/api/firs/{id}/train` | ✅ | Re-run NLP pipeline |
| `POST` | `/api/analysis/analyze-fir` | ✅ | Full AI analysis (inline) |
| `GET` | `/api/analysis/similar/{id}` | ✅ | Semantic similar FIRs |
| `POST` | `/api/legal/search` | ✅ | IPC/CrPC/BNS/judgment search |
| `GET` | `/api/patterns/mo-alerts` | ✅ | Live MO pattern alerts |
| `GET` | `/api/dashboard/stats` | ✅ | Live dashboard numbers |
| `GET` | `/api/dashboard/chroma-stats` | ✅ | ChromaDB index count |
| `POST` | `/api/bhashini/translate` | ✅ | English ↔ Malayalam translation |
| `GET` | `/api/health` | ❌ | Health check |

---

## How the AI Pipeline Works

When an officer uploads a FIR, here is the exact sequence:

```
Officer uploads FIR text/PDF
         │
         ▼
  pdfplumber extracts text (if PDF)
         │
         ▼
  FIR saved to PostgreSQL (status: pending)
         │
         ▼
  BackgroundTask: ingest_fir() runs
         │
    ┌────┴────────────────────────────────────────┐
    │                                              │
    ▼                                              ▼
spaCy NER runs on text              sentence-transformer encodes
(extracts PERSON, GPE, DATE)         FIR text → 384-dim vector
    │                                              │
    ▼                                              ▼
IPC rule engine scores each        ChromaDB.upsert(fir_id, vector, metadata)
section against keywords                           │
(returns top 5 with confidence)          FIR is now searchable
    │
    ▼
Risk level determined
(critical/high/medium/low)
    │
    ▼
MO pattern detected
(regex/keyword cluster matching)
    │
    ▼
AI summary generated
(structured sentence using entities + IPC)
    │
    ▼
FIR record updated in PostgreSQL
(status: indexed, all fields populated)
```

When another FIR is uploaded later, its vector is compared against all existing vectors in ChromaDB via HNSW approximate nearest neighbour search — returning the most semantically similar cases with a similarity score.

---

## Data Flow — Request Lifecycle

### Login Flow
```
User enters KP001 + test1234
    → Login.jsx calls AuthContext.login()
        → authAPI.login() sends POST /api/auth/login
            → Axios interceptor adds Content-Type header
            → Vite proxy (dev) or Nginx (prod) forwards to backend:8000
                → auth.py looks up Officer by badge_number in PostgreSQL
                → bcrypt.checkpw() verifies password hash
                → create_access_token() generates JWT with {sub: "KP001", role: "sub_inspector"}
                → Returns {access_token: "eyJ...", officer: {id, name, station, ...}}
            ← Response travels back through proxy
        ← AuthContext stores token in localStorage, sets officer state
    ← App.jsx re-renders: officer is now set
    ← /login route condition: officer ? Navigate("/") : Login
    ← User is redirected to Dashboard
```

### FIR Analysis Flow
```
Officer pastes FIR text → clicks "Analyse"
    → FIRAnalysis.jsx calls analysisAPI.analyzeFIR(text)
        → Axios adds JWT: "Authorization: Bearer eyJ..."
        → POST /api/analysis/analyze-fir { text: "...", language: "en" }
            → analysis.py:
                1. nlp_service.extract_entities(text)
                   → spaCy finds PERSON/GPE/DATE entities
                   → regex finds weapon, vehicle, property
                2. nlp_service.suggest_ipc_sections(text, entities)
                   → scores 24 IPC sections by keyword match
                   → returns top 5 with confidence scores
                3. nlp_service.get_crime_category() → "Property"
                4. nlp_service.get_risk_level() → "high"
                5. nlp_service.detect_mo_pattern() → "House Breaking"
                6. nlp_service.generate_summary() → structured text
                7. nlp_service.generate_next_steps() → ["Secure scene", ...]
                8. embedding_service.embed(text) → [0.12, -0.34, ...] (384 floats)
                9. chroma_service.search_similar(vector, k=5)
                   → HNSW approximate nearest neighbor search
                   → returns [{fir_id, similarity: 0.87, metadata}, ...]
                10. For each similar FIR: fetch snippet from PostgreSQL
            → Returns AnalysisResponse JSON
        ← FIRAnalysis.jsx renders results:
           entities, IPC sections with animated bars,
           similar cases panel, risk badge, next steps
```

### Legal Search Flow
```
Officer types "bail provisions for non-bailable offence"
    → LegalAssistant.jsx calls legalAPI.search(query)
        → POST /api/legal/search { query: "...", category: null }
            → legal.py:
                1. Loads ALL_LEGAL (IPC + CrPC + judgments + MVA + BNS + POCSO + DV)
                2. For each item: count keyword matches + title match
                3. Sort by score, return top 5
                4. Format: top answer + related sections + citations
            → Returns LegalSearchResponse
        ← LegalAssistant.jsx renders answer in chat bubble
           with citations and related sections
```

---

## Design Decisions & Why

### Why FastAPI over Django/Flask?
- **Async natively** — PostgreSQL (asyncpg), HTTP calls (httpx), all non-blocking
- **Auto-generated API docs** — Swagger UI at `/api/docs` for free
- **Pydantic validation** — request/response models with automatic 422 errors
- **Dependency injection** — `Depends(get_current_officer)` enforces auth cleanly

### Why ChromaDB over Pinecone/Weaviate?
- **Self-hosted** — no API costs, runs in Docker
- **Simple** — HTTP client, one collection, cosine distance
- **Good enough** — for thousands of FIRs, HNSW ANN is plenty fast

### Why Rule-Based IPC Classification Instead of a Fine-Tuned LLM?
- **Deterministic** — same input always gives same output (critical for legal advice)
- **Explainable** — can show exactly which keywords triggered which section
- **No hallucination risk** — never suggests a non-existent IPC section
- **Fast** — no GPU needed, runs in milliseconds
- **Easily extensible** — add a new section by adding a dict to `IPC_KNOWLEDGE_BASE`

### Why `paraphrase-multilingual-MiniLM-L12-v2`?
- **Multilingual** — handles English and Malayalam in the same vector space
- **Small** — ~90 MB, loads fast, runs on CPU
- **Good quality** — excellent for semantic similarity at this scale
- **384 dimensions** — compact enough for ChromaDB without PCA reduction

### Why Singleton Services?
- `NLPService`, `EmbeddingService`, `ChromaService`, `BhashiniService` are all singletons
- ML models are expensive to load (spaCy: ~200ms, sentence-transformer: ~2s)
- Load once at startup, reuse across all requests

### Why localStorage for Auth Instead of HttpOnly Cookies?
- **Simpler** — Axios interceptor attaches token automatically
- **SPA-friendly** — no CSRF complexity
- **Trade-off acknowledged** — vulnerable to XSS, but acceptable for an internal police tool on trusted machines

### Why Celery + Redis AND BackgroundTasks?
- **BackgroundTasks** — for single FIR uploads (lightweight, in-process)
- **Celery** — for bulk re-training, retry logic, and distributed processing when deploying across multiple servers

---

## First-Time Usage

1. Start the system (Docker or manual)
2. Open http://localhost:5173
3. Seed demo credentials: run `curl -X POST http://localhost:8000/api/auth/seed-demo`
4. Login as `KP001` / `test1234`
5. Go to **FIR Analysis** → paste or upload a FIR → click **"Run AI Analysis"**
6. See entities, IPC sections, risk level, and investigation steps
7. Enable **"Save & Index"**, fill in case number/district/station, and click Analyse again to store in DB
8. Go to **Case Intelligence** → see the FIR appear in the list
9. Click **"Find Similar"** — currently empty since only one FIR is indexed
10. Upload 2–3 more FIRs → similar cases will start appearing
11. Go to **Legal Assistant** → type *"bail provisions 167 CrPC"* and press Send
12. Go to **Malayalam FIR** → fill in the form → click Generate Malayalam FIR

---

## License

This project is built for educational and internal demonstration purposes for the Kerala Police department.
