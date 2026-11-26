# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). **Milestone 1** delivers local Postgres, migrations, org-scoped demo auth, and seeded fictional data. Full scheduling, offline sync, signature capture, and real AI report generation are **not** implemented yet (see backlog).

## Purpose

- Dispatcher web: customers, work orders, schedule board, assets, service reports (CRUD/board → M2)
- Technician mobile (Android first via KMP): agenda, job status, checklist (→ M2+)
- Differentiator target: **Service Memory** — recurring failure search/summary (→ M3)

## Stack

| Layer | Technology |
| --- | --- |
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL (Docker Compose, host port **5434**) |
| Mobile | Kotlin Multiplatform shared logic + native Android UI (iOS UI later) |
| AI | `AIProvider` + `DemoAIProvider`; Ollama adapter stub; no paid APIs |

## Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 20+
- Android Studio / JDK 17 (mobile; optional for M1)
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

Postgres listens on `localhost:5434` (avoids clashes with sibling products).

### 3. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
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

Open `http://localhost:3003` — demo login works against seeded users. Feature routes still show **Coming Soon** for full CRUD/dispatch (M2).

### 5. Mobile (Android) — optional for M1

```bash
cd mobile
# Open in Android Studio, or:
./gradlew :androidApp:assembleDebug
```

Shared KMP module exposes agenda stubs; Android app shell shows technician agenda placeholder. iOS UI is deferred.

## Tests

```bash
cd backend
# DB must be up, migrated, and seeded
pytest -q
```

Smoke coverage: `/health`, demo login (≥2 roles), org-scoped customers/work-orders tenant isolation.

## AI

- Default: `AI_PROVIDER=demo` → deterministic `DemoAIProvider` (no network)
- Optional: `AI_PROVIDER=ollama` + local Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`)
- Backend-only calls; typed schemas; AI never completes jobs, certifies safety, or signs for customers
- Endpoints stubbed under `/api/v1/ai/*` (real generation → M3)

## Demo credentials

All passwords: `demo` (fictional data only).

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@demo.local | demo |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |
| Technician | tech2@demo.local … tech5@demo.local | demo |
| Other tenant (isolation) | other@demo.local | demo |

### Demo steps (Milestone 1)

1. `docker compose up -d` → `alembic upgrade head` → `python -m scripts.seed`
2. Start API on port 8003; confirm `GET /health` → `{"status":"ok",...}`
3. `POST /api/v1/auth/demo-login` with `dispatcher@demo.local` / `demo`
4. `GET /api/v1/customers` with `Authorization: Bearer <token>` → 12 customers
5. Login as `other@demo.local` → customers list shows only the other-tenant row
6. `GET /api/v1/work-orders` as tech → 20 jobs for the demo org
7. Web login at `http://localhost:3003/login` with the same credentials

## Seed contents

- 12 customers + service locations
- 15 assets
- 20 work orders across statuses with assignments
- 5 technicians (+ admin + dispatcher)
- Checklist stubs, job activity history, time entries, parts used, attachment metadata, signoffs, audit events
- Second org (`other@demo.local`) for tenant isolation tests

## Milestones / backlog

### M1 — Foundation (this milestone)

- [x] `.env.example` + Docker Compose Postgres
- [x] SQLAlchemy models for core entities
- [x] Alembic migrations
- [x] Demo login + ≥2 roles + org scoping
- [x] Seed dataset (≥12/15/20/5)
- [x] `/health` + auth/tenant smoke tests
- [x] README + backlog

### M2 — Core workflow

- [ ] Full CRUD for customers, locations, assets, work orders
- [ ] Dispatch board + assignment/reassignment + overlap warnings
- [ ] Technician agenda (web + KMP Android) from same backend
- [ ] Status transitions, checklist completion, notes, time entries, parts
- [ ] Attachment upload adapter (metadata already in schema)
- [ ] Printable service report (browser print)

### M3 — AI + differentiator

- [ ] Real Ollama path behind `AIProvider` (DemoAIProvider remains default)
- [ ] Structured editable service report from notes/transcript
- [ ] Job prep summary from asset history/checklist
- [ ] **Service Memory** search + summarize recurring failures (sources + confirmation)

### M4 — Polish

- [ ] Offline notes/checklist/status draft queue + conflict UI
- [ ] Signature capture UI (acknowledgement label)
- [ ] Customer read-only job-status link
- [ ] iOS UI layer
- [ ] E2E / scripted demo recording
- [ ] Lint/format/type gates expanded

## Limitations (current)

- No full scheduling / overlap warnings
- No offline sync queue
- No signature capture UI (seeded signoff rows only)
- No real AI report generation (stubs only)
- Auth is demo bearer tokens — not production-secure
- Mobile run can wait; web Coming Soon for most feature pages
- Prototype security: local demo secrets in `.env` only

## API groups

| Group | Prefix | M1 status |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Demo login + `/me` |
| Customers | `/api/v1/customers` | Org-scoped list |
| Work orders | `/api/v1/work-orders` | Org-scoped list |
| Service locations / assets / schedule / assignments / checklists / time / parts / attachments / reports / AI | `/api/v1/*` | Coming Soon stubs |

Shared conventions: REST JSON, pagination on lists, error shape `{error:{code,message,details}}`, tenant authorization on business endpoints.
