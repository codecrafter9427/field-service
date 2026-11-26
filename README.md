# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). **Milestone 2** delivers customers/locations/work-order CRUD, technician assignment, schedule overlap warnings, and dispatcher web workflow (notes / checklist / time). Offline sync, signature capture, printable polish, and AI service reports remain later milestones.

## Purpose

- Dispatcher web: customers, work orders, schedule board with overlap warnings, job notes/checklist/time
- Technician agenda API (same backend); Android run can wait
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
- Android Studio / JDK 17 (mobile; optional for M2)
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

Health: `GET http://localhost:8003/health` → `milestone: "2"`  
OpenAPI: `http://localhost:8003/docs`

### 4. Web

```bash
cd web
npm install
npm run dev -- --port 3003
```

Open `http://localhost:3003` — demo login works. Dispatcher can create customers/locations/jobs, assign technicians, and see schedule overlap warnings.

### 5. Mobile (Android) — optional / deferred for M2

```bash
cd mobile
# Open in Android Studio, or:
./gradlew :androidApp:assembleDebug
```

Shared KMP module still exposes agenda stubs; wire to `/assignments/agenda` in a later mobile pass.

## Tests

```bash
cd backend
# DB must be up, migrated, and seeded
pytest -q
```

Coverage: `/health`, demo login, tenant isolation, customer/location/work-order CRUD isolation, schedule overlap warnings, agenda visibility for dispatcher-created jobs.

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

### Demo steps (Milestone 2)

1. `docker compose up -d` → `alembic upgrade head` → `python -m scripts.seed`
2. Start API on port 8003; confirm `GET /health` → `{"status":"ok","milestone":"2",...}`
3. `POST /api/v1/auth/demo-login` with `dispatcher@demo.local` / `demo`
4. Create a work order with `scheduled_start` / `scheduled_end` and `technician_id` for Terry Technician
5. Create a second overlapping job for the same technician → response includes `overlap_warning: true`
6. `GET /api/v1/assignments/agenda` as `tech@demo.local` → new job is visible
7. `GET /api/v1/schedule` → overlapping rows flagged
8. Web: login at `http://localhost:3003/login` → Work Orders → create/assign → Schedule shows warnings

## Seed contents

- 12 customers + service locations
- 15 assets
- 20 work orders across statuses with assignments and scheduled windows
- 5 technicians (+ admin + dispatcher)
- Checklist stubs, job activity history, time entries, parts used, attachment metadata, signoffs, audit events
- Second org (`other@demo.local`) for tenant isolation tests

## Milestones / backlog

### M1 — Foundation

- [x] `.env.example` + Docker Compose Postgres
- [x] SQLAlchemy models for core entities
- [x] Alembic migrations
- [x] Demo login + ≥2 roles + org scoping
- [x] Seed dataset (≥12/15/20/5)
- [x] `/health` + auth/tenant smoke tests
- [x] README + backlog

### M2 — Core workflow (this milestone)

- [x] Full CRUD for customers, service locations, work orders
- [x] Assign / reassign technician + schedule list with overlap warnings
- [x] Technician agenda API (`/assignments/agenda`)
- [x] Status transitions, checklist completion, notes, time entries
- [x] Org-scoped auth on business endpoints + overlap/tenant tests
- [x] Dispatcher web views (customers, work orders, schedule)
- [ ] Attachment upload adapter (metadata already in schema) — deferred polish
- [ ] Printable service report — deferred
- [ ] Android agenda UI run — deferred

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

- No offline sync queue
- No signature capture UI (seeded signoff rows only)
- No printable service-report polish
- No real AI report generation (stubs only)
- Assets / parts / attachments / reports still Coming Soon or metadata-only
- Auth is demo bearer tokens — not production-secure
- Mobile Android run deferred; agenda available via API
- Prototype security: local demo secrets in `.env` only

## API groups

| Group | Prefix | M2 status |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Demo login + `/me` |
| Customers | `/api/v1/customers` | Full CRUD (archive delete) |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Work orders | `/api/v1/work-orders` | CRUD + assign + notes + activities |
| Schedule | `/api/v1/schedule` | List + overlap warnings |
| Assignments | `/api/v1/assignments` | Create, list, technicians, agenda |
| Checklists | `/api/v1/checklists` | Create + item complete |
| Time entries | `/api/v1/time-entries` | Create + update |
| Assets / parts / attachments / reports / AI | `/api/v1/*` | Coming Soon stubs |

Shared conventions: REST JSON, pagination on lists, error shape `{error:{code,message,details}}`, tenant authorization on business endpoints. Overlap is a **warning** (assignment still succeeds) when the same technician has overlapping `scheduled_start`/`scheduled_end` windows.
