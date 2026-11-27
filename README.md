# Field Service

Scheduling, dispatch, and job execution MVP for maintenance, repair, and installation businesses.

Portfolio product (Agent C). **Milestone 6** adds a secure customer job-status portal, signed staff tokens, rate limits, backup/CI docs, and a read-only Insights connector. Preserves M5 offline notes/checklist/status sync. No paid APIs.

## Purpose

- Dispatcher web: customers, work orders, schedule overlap warnings, parts, printable reports
- Customer **acknowledgement** capture (explicitly not certified e-sign) with server timestamp
- Customer **read-only job-status links** (expiring / revocable)
- Assets CRUD + service history by customer/asset
- Labor / parts summary reports + Insights connector aggregates
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

Health: `GET http://localhost:8003/health` → `milestone: "6"`  
OpenAPI: `http://localhost:8003/docs`

### 4. Web

```bash
cd web
npm install
npm run dev -- --port 3003
```

Open `http://localhost:3003` — demo login works. Seeded customer status page: `/status/demo-portal-status-token-m6-northwind`.

### 5. Mobile (Android) — optional

See [`mobile/README.md`](mobile/README.md). Access tokens are **opaque** HMAC-signed strings (M6); treat as bearer values only — do not parse.

## Tests & quality gates

```bash
cd backend
# DB must be up, migrated, and seeded
pytest -q

cd ../web
npm run lint
npm run typecheck
```

CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (pytest + web lint/typecheck).  
Backup/restore: [`BACKUP.md`](BACKUP.md). Insights contract: [`CONNECTORS.md`](CONNECTORS.md).

## Demo vs production

| Mode | Guidance |
| --- | --- |
| Demo (default) | `DEMO_AUTH_ENABLED=true`, placeholder `SECRET_KEY` allowed (startup warning) |
| Hardened / prod-like | `ENVIRONMENT=production` or `DEMO_AUTH_ENABLED=false` → **startup fails** if `SECRET_KEY` is still a placeholder; set a strong secret; password policy ≥8 chars when demo auth is off |

Staff tokens expire per `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480). No refresh endpoint — re-login. Login + public portal resolve are rate-limited (in-process).

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

### Demo steps (Milestone 6)

1. Start DB → migrate → seed → API `:8003` → web `:3003`
2. Open seeded status page `/status/demo-portal-status-token-m6-northwind` (no login)
3. Login as dispatcher → Work Orders → **Customer status link** → create/copy → revoke
4. Confirm technician cannot create portal links (403)
5. Optional: Insights `GET /api/v1/connectors/insights/v1/summary` with dispatcher Bearer
6. M5 regression: Android offline note/checklist/status drain still works

## Seed contents

- 12 customers + service locations
- 15 assets
- 20 work orders with recurring filter/leak history notes for Service Memory
- 5 technicians (+ admin + dispatcher)
- Checklists, activities, time entries, parts, attachment metadata, signoffs, audit events
- One active **customer portal link** for DEMO
- Second org (`other@demo.local`) for tenant isolation tests

## Milestones / backlog

### M1 — Foundation

- [x] Docker Compose Postgres, models, Alembic, demo auth, seed, health/tests

### M2 — Core workflow

- [x] Customers/locations/work orders CRUD, assign, overlap warnings, agenda API, dispatcher web

### M3 — AI + Service Memory

- [x] DemoAIProvider + optional Ollama, service report/job prep/Service Memory + web UI + tests

### M4 — Polish

- [x] Printable service report, acknowledgement signoff, assets CRUD, labor/parts reports, KMP clients

### M5 — Offline sync

- [x] Offline UUID op queue + reconnect drain (notes / checklist / status)
- [x] Note `client_operation_id` idempotency + status/checklist `base_updated_at` → 409
- [x] Android sync badges + conflict resolve

### M6 — Portal + hardening + Insights (this milestone)

- [x] Customer portal links (hash at rest, expiry, revoke) + public redacted job-status
- [x] Web `/status/[token]` + dispatcher create/copy/revoke UI
- [x] Signed staff tokens (`ACCESS_TOKEN_EXPIRE_MINUTES`); PBKDF2 with iterations; login/portal rate limits
- [x] `require_roles` on portal admin + Insights connector; audit create/revoke/deny
- [x] Insights connector `/api/v1/connectors/insights/v1/*` + `CONNECTORS.md`
- [x] `BACKUP.md`, CI workflow, env guards, milestone `6` / API `0.6.0`
- [ ] iOS UI layer (backlog)
- [ ] Offline attachments / signoff / time (out of scope)
- [ ] Certified e-sign / paid PDF (out of scope)

## Limitations (current)

- Acknowledgement is **not** a certified electronic signature
- Print uses browser Print / Save as PDF — no server-side PDF engine
- Offline sync covers notes/checklist/status only (no attachments/signoff/time offline)
- Auth is portfolio-grade HMAC bearer tokens — not a full IdP
- In-memory rate limits reset per process
- Android device run optional; iOS HTTP transport stubbed
- Attachment binary upload still metadata/Coming Soon
- Prototype security: local demo secrets in `.env` only

## API groups

| Group | Prefix | M6 status |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Signed login + `/me` |
| Customers | `/api/v1/customers` | CRUD + `/service-history` |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Full CRUD + `/service-history` |
| Work orders | `/api/v1/work-orders` | CRUD + assign + notes + activities |
| Portal links | `/api/v1/work-orders/{id}/portal-links` | Create/list (admin/dispatcher) |
| Portal revoke | `/api/v1/portal-links/{id}/revoke` | Admin/dispatcher |
| Public job status | `/api/v1/public/job-status` | Token query; redacted |
| Signoffs | `/api/v1/work-orders/{id}/signoffs` | Create/list acknowledgement |
| Schedule | `/api/v1/schedule` | List + overlap warnings |
| Assignments | `/api/v1/assignments` | Create, list, technicians, agenda |
| Checklists | `/api/v1/checklists` | Create + item complete |
| Time entries | `/api/v1/time-entries` | Create + update |
| Parts used | `/api/v1/parts-used` | List + create |
| Reports | `/api/v1/reports/service` | Summary + printable job payload |
| Insights connector | `/api/v1/connectors/insights/v1` | health + summary (+ splits) |
| AI | `/api/v1/ai/*` | Service report, job prep, Service Memory |
| Attachments | `/api/v1/attachments` | Coming Soon stub |

Shared conventions: REST JSON, pagination on lists, error shape `{error:{code,message,details}}`, tenant authorization on business endpoints.

**M5 sync contract (unchanged):** notes accept optional `client_operation_id` (idempotent per org); status PATCH requires `base_updated_at`; checklist item PATCH requires `base_updated_at`. Stale base → `409` with `{error:{code:"conflict", details:{server}}}`.
