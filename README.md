# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). **Milestone 3** delivers AI service reports, job prep, checklist suggestions (confirm-only), and **Service Memory** (recurring-failure search + summary). DemoAIProvider works without Ollama. Offline sync, signature capture, and printable polish remain later milestones.

## Purpose

- Dispatcher web: customers, work orders, schedule overlap warnings, job notes/checklist/time
- AI Assist: editable service-report drafts, job prep, Service Memory
- Technician agenda API (same backend); Android run can wait
- Differentiator: **Service Memory** — recurring failure search/summary from recorded history

## Stack

| Layer | Technology |
| --- | --- |
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL (Docker Compose, host port **5434**) |
| Mobile | Kotlin Multiplatform shared logic + native Android UI (iOS UI later) |
| AI | `AIProvider` + `DemoAIProvider` (default); optional local Ollama adapter; no paid APIs |

## Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 20+
- Android Studio / JDK 17 (mobile; optional)
- Optional: [Ollama](https://ollama.com) with a local open model (not required)

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

Health: `GET http://localhost:8003/health` → `milestone: "3"`  
OpenAPI: `http://localhost:8003/docs`

### 4. Web

```bash
cd web
npm install
npm run dev -- --port 3003
```

Open `http://localhost:3003` — demo login works. Use **AI Assist** for service report, job prep, and Service Memory.

### 5. Mobile (Android) — optional / deferred

```bash
cd mobile
# Open in Android Studio, or:
./gradlew :androidApp:assembleDebug
```

## Tests

```bash
cd backend
# DB must be up, migrated, and seeded
pytest -q
```

Coverage: `/health`, demo login, tenant isolation, CRUD, schedule overlap, Demo AI structured drafts, Service Memory retrieval, AI auth/tenant gates.

## AI setup (works without Ollama)

Default configuration needs **no model download and no network**:

```env
AI_PROVIDER=demo
```

`DemoAIProvider` returns deterministic structured drafts for:

| Endpoint | Behavior |
| --- | --- |
| `POST /api/v1/ai/service-report` | Editable draft: problem, diagnosis, work, parts, follow-up |
| `POST /api/v1/ai/service-report/approve` | Stores human-edited report as attachment metadata + audit; **does not** complete job or create signoff |
| `POST /api/v1/ai/job-prep` | Asset/customer history summary + checklist suggestions by job type |
| `POST /api/v1/ai/job-prep/confirm-checklist` | Adds only technician-confirmed items |
| `POST /api/v1/ai/service-memory` | Search recurring failures; AI summarizes recorded history + suggests follow-up (confirm before acting) |

Rules: backend-only model calls; typed schemas; AI never completes jobs, certifies safety, or signs for customers. Generated content is labeled; sources shown where possible.

### Optional Ollama

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Install Ollama, pull a local open model (`ollama pull llama3.2`), then restart the API. If Ollama is unreachable or generation fails, the adapter **falls back to DemoAIProvider** so demos still work.

## Demo credentials

All passwords: `demo` (fictional data only).

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@demo.local | demo |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |
| Technician | tech2@demo.local … tech5@demo.local | demo |
| Other tenant (isolation) | other@demo.local | demo |

### Demo steps (Milestone 3)

1. `docker compose up -d` → `alembic upgrade head` → `python -m scripts.seed`
2. Start API on port 8003; confirm `GET /health` → `{"milestone":"3",...}`
3. Web: login as `dispatcher@demo.local` / `demo` at `http://localhost:3003/login`
4. **AI Assist → Service report**: pick a work order, add notes (e.g. filter clog), Generate draft → edit fields → Approve edited report (status unchanged)
5. **Job prep**: prepare an HVAC job → select suggested checklist items → Confirm selected items
6. **Service Memory**: query `filter` (optionally pick Rooftop HVAC) → review recurring themes, sources, and suggested follow-up
7. API: `POST /api/v1/ai/service-memory` with `{ "query": "filter" }` as dispatcher also returns hits + themes

## Seed contents

- 12 customers + service locations
- 15 assets (read via `/assets`)
- 20 work orders with recurring filter/leak history notes for Service Memory
- 5 technicians (+ admin + dispatcher)
- Checklists, activities, time entries, parts, attachment metadata, signoffs, audit events
- Second org (`other@demo.local`) for tenant isolation tests

## Milestones / backlog

### M1 — Foundation

- [x] `.env.example` + Docker Compose Postgres
- [x] SQLAlchemy models for core entities
- [x] Alembic migrations
- [x] Demo login + ≥2 roles + org scoping
- [x] Seed dataset (≥12/15/20/5)
- [x] `/health` + auth/tenant smoke tests

### M2 — Core workflow

- [x] Full CRUD for customers, service locations, work orders
- [x] Assign / reassign technician + schedule list with overlap warnings
- [x] Technician agenda API (`/assignments/agenda`)
- [x] Status transitions, checklist completion, notes, time entries
- [x] Dispatcher web views (customers, work orders, schedule)

### M3 — AI + differentiator (this milestone)

- [x] `AIProvider` + `DemoAIProvider` + optional Ollama adapter (with demo fallback)
- [x] Structured editable service report + approve gate (no auto-complete / sign)
- [x] Job prep from asset history/checklist + job-type suggestions (confirm-only)
- [x] **Service Memory** search + summarize recurring failures (sources + confirmation)
- [x] Web UI for report draft, job prep, Service Memory
- [x] Tests for demo AI, Service Memory retrieval, AI auth/tenant
- [x] README AI setup without Ollama

### M4 — Polish

- [ ] Offline notes/checklist/status draft queue + conflict UI
- [ ] Signature capture UI (acknowledgement label)
- [ ] Customer read-only job-status link
- [ ] Printable service-report polish
- [ ] Assets write CRUD
- [ ] iOS UI layer / Android agenda UI run
- [ ] E2E / scripted demo recording

## Limitations (current)

- No offline sync queue
- No signature capture UI (seeded signoff rows only)
- No printable service-report polish
- Assets are read-only list (write CRUD later)
- Auth is demo bearer tokens — not production-secure
- Mobile Android run deferred; agenda available via API
- Ollama path is optional; default demos use DemoAIProvider
- Prototype security: local demo secrets in `.env` only

## API groups

| Group | Prefix | M3 status |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Demo login + `/me` |
| Customers | `/api/v1/customers` | Full CRUD |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Read list/detail |
| Work orders | `/api/v1/work-orders` | CRUD + assign + notes + activities |
| Schedule | `/api/v1/schedule` | List + overlap warnings |
| Assignments | `/api/v1/assignments` | Create, list, technicians, agenda |
| Checklists | `/api/v1/checklists` | Create + item complete |
| Time entries | `/api/v1/time-entries` | Create + update |
| AI | `/api/v1/ai/*` | Service report, job prep, Service Memory |
| Parts / attachments / reports | `/api/v1/*` | Coming Soon or metadata-only |

Shared conventions: REST JSON, pagination on lists, error shape `{error:{code,message,details}}`, tenant authorization on business endpoints.
