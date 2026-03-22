# Kerala Police AI Investigation Assistant (KPAIA)

A production-grade full-stack AI system for Kerala Police officers — providing real-time FIR analysis, semantic case search, MO pattern detection, legal guidance, and Malayalam FIR drafting.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [How to Run](#how-to-run)
   - [Option A — Docker (recommended)](#option-a--docker-recommended)
   - [Option B — Manual (local dev)](#option-b--manual-local-dev)
5. [Environment Variables](#environment-variables)
6. [Backend — Detailed Code Walkthrough](#backend--detailed-code-walkthrough)
7. [Frontend — Detailed Code Walkthrough](#frontend--detailed-code-walkthrough)
8. [API Reference](#api-reference)
9. [How the AI Pipeline Works](#how-the-ai-pipeline-works)
10. [First-Time Usage](#first-time-usage)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│           React + Vite + Tailwind Frontend        │
│      Officer Login · Dashboard · FIR Analysis    │
│   Case Intelligence · Legal Chat · Malayalam FIR │
└─────────────────────┬────────────────────────────┘
                      │  REST API (JSON over HTTP)
                      │  Vite dev proxy → localhost:8000
┌─────────────────────▼────────────────────────────┐
│               FastAPI Backend (Python)            │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ FIR API  │  │ Analysis │  │  Legal / MO    │  │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │             │                 │            │
│  ┌────▼──────┐ ┌────▼───────┐ ┌──────▼────────┐  │
│  │PostgreSQL │ │  ChromaDB  │ │ Bhashini API  │  │
│  │(Case DB)  │ │(FIR vectors│ │  (Malayalam)  │  │
│  └───────────┘ └────────────┘ └───────────────┘  │
│                      │                            │
│               ┌──────▼────────┐                   │
│               │  Celery+Redis │ (async training)  │
│               └───────────────┘                   │
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
| Auth | JWT (python-jose) + bcrypt (passlib) | Stateless officer login |
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
│       │   ├── legal.py        ← IPC/CrPC/judgment search
│       │   ├── patterns.py     ← MO pattern clustering
│       │   ├── dashboard.py    ← Live stats
│       │   └── bhashini.py     ← Translation proxy
│       │
│       └── tasks/
│           └── train_pipeline.py   ← Celery async task wrapper
│
├── tests/
│   ├── test_auth.py            ← Pytest auth endpoint tests
│   └── sample_fir.txt          ← Realistic FIR for testing
│
└── frontend/
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
        │   └── Layout.jsx      ← Collapsible sidebar + topbar wrapper
        │
        └── pages/
            ├── Login.jsx           ← Officer login (badge + password)
            ├── Dashboard.jsx       ← Live stats, charts, MO alerts
            ├── FIRAnalysis.jsx     ← Upload/paste FIR → AI analysis
            ├── CaseIntelligence.jsx← Browse indexed FIRs + similarity
            ├── MOPatterns.jsx      ← Crime pattern alerts + detail
            ├── LegalAssistant.jsx  ← Chat UI for IPC/CrPC queries
            └── MalayalamFIR.jsx    ← English form → Malayalam FIR
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
- `get_password_hash()` / `verify_password()` — bcrypt hashing via passlib
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
- 2 SOPs (BPR&D crime scene management, Kerala Police CCTNS)

`search_legal_kb(query)` scores each item by keyword matches + title match and returns the top 5 with a structured answer + citation.

#### `patterns.py`
Defines 6 known MO cluster patterns (OTP fraud, chain snatching, house breaking, etc.). On each request, scans all FIRs in the DB for keyword matches and returns occurrence counts per district. Results are sorted by risk level.

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
- **Sidebar** with collapsible toggle (stores state in component, slides between w-64 and w-16)
- **Active route highlighting** via `useLocation()`
- **Officer card** at the bottom with initials avatar and logout button
- **Topbar** with current page title, system online indicator, and badge number

### Page Components

| Page | What it does |
|---|---|
| `Login.jsx` | Badge/password form → `authAPI.login()`. "Seed Demo" button calls `authAPI.seedDemo()` and pre-fills credentials. |
| `Dashboard.jsx` | On mount fetches `dashboardAPI.getStats()` and `patternsAPI.getMOAlerts()`. Renders Recharts `BarChart` (district breakdown) and `PieChart` (risk distribution). Shows ChromaDB vector count. |
| `FIRAnalysis.jsx` | Drag-and-drop or text input. Optionally saves to DB via `firsAPI.upload()`. Always calls `analysisAPI.analyzeFIR()`. Displays entities, IPC sections with animated confidence bars, similar cases from ChromaDB, and next steps. |
| `CaseIntelligence.jsx` | Left: filterable FIR list from `firsAPI.list()`. Right: detail panel. Clicking a case fetches `analysisAPI.getSimilar()` if indexed. "Re-train" button triggers `firsAPI.train()`. |
| `MOPatterns.jsx` | Fetches all patterns on mount. Left: pattern cards coloured by risk (critical ones animate). Right: detail with description, affected districts, linked FIR UUIDs, and recommended action. |
| `LegalAssistant.jsx` | Chat-style UI. Sends query via `legalAPI.search()`. Renders responses with lightweight markdown parsing (bold, bullet lists). Sidebar of 6 quick-query shortcuts. Shows source citations. |
| `MalayalamFIR.jsx` | Structured form for FIR fields. On submit, assembles English text and calls `bhashiniAPI.translate()`. Renders the Malayalam output in `Noto Sans Malayalam` font with copy/print options. |

---

## API Reference

Full interactive docs at **http://localhost:8000/api/docs** (Swagger UI).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | ❌ | Officer login → JWT |
| `POST` | `/api/auth/seed-demo` | ❌ | Seed demo officers (dev only) |
| `GET` | `/api/auth/me` | ✅ | Current officer info |
| `POST` | `/api/firs/upload` | ✅ | Upload FIR (PDF/text form) |
| `GET` | `/api/firs/` | ✅ | List all FIRs (with filters) |
| `GET` | `/api/firs/{id}` | ✅ | Get single FIR |
| `POST` | `/api/firs/{id}/train` | ✅ | Re-run NLP pipeline |
| `POST` | `/api/analysis/analyze-fir` | ✅ | Full AI analysis (inline) |
| `GET` | `/api/analysis/similar/{id}` | ✅ | Semantic similar FIRs |
| `POST` | `/api/legal/search` | ✅ | IPC/CrPC/judgment search |
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

## First-Time Usage

1. Start the system (Docker or manual)
2. Open http://localhost:5173
3. Click **"Seed Demo Credentials"** on the login page → login as `KP001`
4. Go to **FIR Analysis** → click **"Load Sample"** → click **"Run AI Analysis"**
5. See entities, IPC sections, risk level, and investigation steps
6. Enable **"Save & Index"**, fill in case number/district/station, and click Analyse again to store in DB
7. Go to **Case Intelligence** → see the FIR appear in the list
8. Click **"Find Similar"** — currently empty since only one FIR is indexed
9. Upload 2–3 more FIRs → similar cases will start appearing
10. Go to **Legal Assistant** → type *"bail provisions 167 CrPC"* and press Send
11. Go to **Malayalam FIR** → click Load Sample → Generate Malayalam FIR
