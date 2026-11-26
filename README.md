# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). Skeleton scaffold for local demo — full scheduling, offline sync, signature capture, and real AI report generation are **not** implemented yet.

## Purpose

- Dispatcher web: customers, work orders, schedule board, assets, service reports
- Technician mobile (Android first via KMP): agenda, job status stubs, checklist placeholders
- Differentiator target: **Service Memory** — recurring failure search/summary (stubbed)

## Stack

| Layer | Technology |
| --- | --- |
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL (Docker Compose) |
| Mobile | Kotlin Multiplatform shared logic + native Android UI (iOS UI later) |
| AI | `AIProvider` + `DemoAIProvider`; Ollama adapter stub; no paid APIs |

## Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 20+
- Android Studio / JDK 17 (mobile)
- Optional: [Ollama](https://ollama.com) with a local open model

### 1. Environment

```bash
cd products/field-service
cp .env.example .env
```

### 2. Database

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Migrations / seed are placeholders — wire when models land
# alembic upgrade head
# python -m scripts.seed
uvicorn app.main:app --reload --port 8003
```

Health: `GET http://localhost:8003/health`  
OpenAPI: `http://localhost:8003/docs`

### 4. Web

```bash
cd web
npm install
npm run dev -- --port 3003
```

Open `http://localhost:3003` — demo login placeholder; feature routes show **Coming Soon**.

### 5. Mobile (Android)

```bash
cd mobile
# Open in Android Studio, or:
./gradlew :androidApp:assembleDebug
```

Shared KMP module exposes agenda stubs; Android app shell shows technician agenda placeholder. iOS UI is deferred.

## AI

- Default: `AI_PROVIDER=demo` → deterministic `DemoAIProvider` (no network)
- Optional: `AI_PROVIDER=ollama` + local Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`)
- Backend-only calls; typed schemas; AI never completes jobs, certifies safety, or signs for customers
- Endpoints stubbed under `/api/v1/ai/*`

## Demo credentials (placeholder)

| Role | Email | Password |
| --- | --- | --- |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |

Fictional data only. Seed script is a placeholder until entities are implemented.

## Milestones

1. **Scaffold** (this commit): repo layout, health, API v1 stubs, demo login, Coming Soon, KMP shell, Postgres
2. Core CRUD + dispatch → technician agenda vertical slice
3. AI provider + Demo fallback + Service Memory differentiator
4. Polish, tests, README demo recording

## Limitations (current skeleton)

- No full scheduling / overlap warnings
- No offline sync queue
- No signature capture
- No real AI report generation (stubs only)
- No Alembic models/migrations yet (placeholder env)
- No seeded dataset yet
- iOS UI not started
- Auth is demo placeholder only — not production-secure

## API groups (planned)

`/customers`, `/service-locations`, `/assets`, `/work-orders`, `/schedule`, `/assignments`, `/checklists`, `/time-entries`, `/parts-used`, `/attachments`, `/reports/service`, `/ai/service-report`, `/ai/job-prep`
