# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). **Milestone 5** adds offline notes/checklist/status sync (UUID op queue, reconnect drain, visible conflicts). Builds on M4 dispatcher polish, printable reports, acknowledgement signoff, assets, and KMP agenda clients. No paid APIs.

## Purpose

- Dispatcher web: customers, work orders, schedule overlap warnings, parts, printable reports
- Customer **acknowledgement** capture (explicitly not certified e-sign) with server timestamp
- Assets CRUD + service history by customer/asset
- Labor / parts summary reports
- Technician agenda + job detail API clients (Android Studio sync documented; device run optional)
- Differentiator (M3): **Service Memory** — recurring failure search/summary from recorded history

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

Health: `GET http://localhost:8003/health` → `milestone: "5"`  
OpenAPI: `http://localhost:8003/docs`

### 4. Web

```bash
cd web
npm install
npm run dev -- --port 3003
```

Open `http://localhost:3003` — demo login works.

### 5. Mobile (Android) — optional

See [`mobile/README.md`](mobile/README.md) for Android Studio sync steps.

```bash
cd mobile
# Open folder in Android Studio (JDK 17) → Gradle sync → run androidApp
# Or: ./gradlew :androidApp:assembleDebug
```

Emulator API base: `http://10.0.2.2:8003/api/v1`. Falls back to demo stubs if API is down.

## Tests & quality gates

```bash
cd backend
# DB must be up, migrated, and seeded
pytest -q

cd ../web
npm run lint
npm run typecheck
```

Coverage: `/health` (M5), demo login, tenant isolation, CRUD, schedule overlap, Demo AI, Service Memory, **assets CRUD**, **signoff timestamp**, **parts + labor/parts reports**, printable report payload, **note idempotency + status/checklist 409**.

## AI setup (works without Ollama)

```env
AI_PROVIDER=demo
```

| Endpoint | Behavior |
| --- | --- |
| `POST /api/v1/ai/service-report` | Editable draft |
| `POST /api/v1/ai/service-report/approve` | Stores edited report metadata; does **not** complete/sign |
| `POST /api/v1/ai/job-prep` | History summary + checklist suggestions |
| `POST /api/v1/ai/job-prep/confirm-checklist` | Adds confirmed items only |
| `POST /api/v1/ai/service-memory` | Recurring-failure search + summary |

Optional Ollama: set `AI_PROVIDER=ollama` + local model; falls back to DemoAIProvider on failure.

## Demo credentials

All passwords: `demo` (fictional data only).

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@demo.local | demo |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |
| Technician | tech2@demo.local … tech5@demo.local | demo |
| Other tenant (isolation) | other@demo.local | demo |

Scripted checklist: **[DEMO.md](DEMO.md)**.

### Demo steps (Milestone 5)

1. Start DB → migrate → seed → API `:8003` → web `:3003`
2. Login as dispatcher → dashboard / work orders (regression)
3. Android: airplane mode → queue note + checklist + status → reconnect → **Drain queue**
4. Force conflict: change status on web, then drain a stale mobile status → **Conflict** → Keep local / Take server
5. Optional M4 regression: printable report, acknowledgement, assets, labor/parts reports

## Seed contents

- 12 customers + service locations
- 15 assets
- 20 work orders with recurring filter/leak history notes for Service Memory
- 5 technicians (+ admin + dispatcher)
- Checklists, activities, time entries, parts, attachment metadata, signoffs, audit events
- Second org (`other@demo.local`) for tenant isolation tests

## Milestones / backlog

### M1 — Foundation

- [x] Docker Compose Postgres, models, Alembic, demo auth, seed, health/tests

### M2 — Core workflow

- [x] Customers/locations/work orders CRUD, assign, overlap warnings, agenda API, dispatcher web

### M3 — AI + Service Memory

- [x] DemoAIProvider + optional Ollama, service report/job prep/Service Memory + web UI + tests

### M4 — Polish

- [x] Printable service report via browser print CSS (no paid PDF)
- [x] Acknowledgement signature stub + timestamped signoff API
- [x] Assets CRUD + service history (customer/asset)
- [x] Labor/parts summary reports
- [x] Dispatcher UX polish (dashboard, parts on jobs, report links)
- [x] Lint/typecheck scripts + expanded pytest
- [x] README + DEMO.md
- [x] KMP agenda/job detail API clients + Android Studio sync docs

### M5 — Offline sync (this milestone)

- [x] Offline UUID op queue + reconnect drain (notes / checklist / status)
- [x] Note `client_operation_id` idempotency + status/checklist `base_updated_at` → 409
- [x] Android sync badges + conflict resolve (keep local / take server)
- [x] pytest + queue unit tests + airplane-mode DEMO script
- [ ] Customer read-only job-status link (backlog)
- [ ] iOS UI layer (backlog)
- [ ] Offline attachments / signoff / time (out of scope for M5)
- [ ] Certified e-sign / paid PDF (out of scope)

## Limitations (current)

- Acknowledgement is **not** a certified electronic signature
- Print uses browser Print / Save as PDF — no server-side PDF engine
- Offline sync covers notes/checklist/status only (no attachments/signoff/time offline)
- Auth is demo bearer tokens — not production-secure
- Android device run optional; iOS HTTP transport stubbed
- Attachment binary upload still metadata/Coming Soon
- Prototype security: local demo secrets in `.env` only

## API groups

| Group | Prefix | M5 status |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Demo login + `/me` |
| Customers | `/api/v1/customers` | CRUD + `/service-history` |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Full CRUD + `/service-history` |
| Work orders | `/api/v1/work-orders` | CRUD + assign + notes + activities |
| Signoffs | `/api/v1/work-orders/{id}/signoffs` | Create/list acknowledgement |
| Schedule | `/api/v1/schedule` | List + overlap warnings |
| Assignments | `/api/v1/assignments` | Create, list, technicians, agenda |
| Checklists | `/api/v1/checklists` | Create + item complete |
| Time entries | `/api/v1/time-entries` | Create + update |
| Parts used | `/api/v1/parts-used` | List + create |
| Reports | `/api/v1/reports/service` | Summary + printable job payload |
| AI | `/api/v1/ai/*` | Service report, job prep, Service Memory |
| Attachments | `/api/v1/attachments` | Coming Soon stub |

Shared conventions: REST JSON, pagination on lists, error shape `{error:{code,message,details}}`, tenant authorization on business endpoints.
