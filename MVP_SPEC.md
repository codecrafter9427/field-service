# Field Service — MVP Spec

Skeleton-aligned specification for the portfolio MVP. Full production coverage is out of scope for the first vertical slices.

## Purpose

Scheduling, dispatch, and job execution for maintenance, repair, and installation businesses. Web for dispatchers; KMP Android-first mobile for technicians.

## Roles

| Role | Capabilities |
| --- | --- |
| Admin / Dispatcher | Customers, schedule, assignment, reports, settings |
| Technician | Assigned jobs, checklists, notes, parts, signoff |
| Customer (optional) | Read-only job-status link (backlog M4) |

## Entities (schema)

Organization, User, Customer, ServiceLocation, Asset, WorkOrder (+ `scheduled_start` / `scheduled_end`), WorkOrderAssignment, Checklist, ChecklistItem, JobActivity, TimeEntry, PartUsed, Attachment, CustomerSignoff, AuditEvent.

UUID primary keys, UTC timestamps, organization-scoped rows, archive preferred over hard-delete.

## Work order statuses

Draft → Scheduled → En Route → In Progress → Waiting for Parts → Completed / Cancelled

## API groups

| Group | Prefix | Status |
| --- | --- | --- |
| Auth (demo) | `/api/v1/auth` | Demo login + `/me` (DB-backed, org-scoped) |
| Customers | `/api/v1/customers` | Full CRUD |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Read list/detail (write CRUD later) |
| Work orders | `/api/v1/work-orders` | Full CRUD + assign + notes + activities |
| Schedule | `/api/v1/schedule` | List with overlap warnings |
| Assignments | `/api/v1/assignments` | Create/list/technicians/agenda |
| Checklists | `/api/v1/checklists` | Create + item patch |
| Time entries | `/api/v1/time-entries` | Create + update |
| Parts used | `/api/v1/parts-used` | Coming Soon stub |
| Attachments | `/api/v1/attachments` | Coming Soon stub |
| Reports | `/api/v1/reports/service` | Coming Soon stub |
| AI service report | `/api/v1/ai/service-report` | Draft + approve (human edit required) |
| AI job prep | `/api/v1/ai/job-prep` | History summary + confirm checklist |
| AI Service Memory | `/api/v1/ai/service-memory` | Recurring-failure search + summarize |
| Health | `/health` | Implemented (milestone 3) |

Shared conventions: REST JSON, pagination/search/sort on lists, error shape `{error:{code,message,details}}`, tenant authorization on every business endpoint.

Overlap rule: when assigning or creating with a technician and both jobs have `scheduled_start`/`scheduled_end`, the API **warns** (`overlap_warning` + overlapping IDs) if intervals overlap for the same technician. Cancelled jobs are excluded. Assignment is not blocked.

## Web baseline

**M2:** dashboard snapshot, customer + location directory, work-order create/assign/status, notes/checklist/time panels, schedule list with overlap badges.

**M3:** AI Assist page — service report draft/approve, job prep + checklist confirm, Service Memory search UI; assets read list.

Still later: asset write CRUD, printable service report polish, full calendar board chrome, parts UI.

## Mobile baseline

- Technician agenda API ready (`GET /assignments/agenda`)
- Android UI run deferred
- Offline drafts / signature capture → M4

## AI (M3)

- Structured editable service report from notes/transcript
- Job prep summary from asset history/checklist
- Checklist suggestions by job type (technician confirms)
- Rules: backend-only; DemoAIProvider if Ollama absent; never complete job / certify safety / sign for customer
- Optional Ollama adapter with demo fallback

## Differentiator — Service Memory

Search recurring failures by asset/customer. AI summarizes repeated issues and suggests maintenance follow-up from **recorded history** only. Show sources; require human confirmation before creating follow-up work. Seeded job history includes filter/leak themes for demos.

## Acceptance criteria

### Milestone 1 (done)

1. Local Postgres via Docker Compose; `.env.example` documented
2. Alembic migrations apply cleanly
3. Seed creates ≥12 customers, 15 assets, 20 jobs, 5 technicians + history
4. Demo login works for ≥2 roles; tokens are org-scoped
5. `/health` OK; auth + tenant smoke tests pass
6. No paid APIs required

### Milestone 2 (done)

1. Customers + service locations CRUD (org-scoped)
2. Work orders CRUD with statuses; assign technician
3. Schedule/list warns on overlapping jobs for same technician (server-side)
4. Job notes / checklist / time entry basic APIs + dispatcher web views
5. API tests cover overlap warning + tenant isolation
6. README demo: dispatcher creates job → visible in assignments/agenda API

### Milestone 3 (done when)

1. AIProvider + DemoAIProvider + optional Ollama adapter (demo fallback)
2. Service report draft editable; approve stores metadata without completing/signing
3. Job prep from history/checklist; suggestions require confirm
4. Service Memory search + AI summary with sources
5. Web UI for report, job prep, Service Memory
6. Tests for demo AI, Service Memory retrieval, AI auth
7. README documents AI setup without Ollama

### Full MVP vertical slice (later milestones)

1. Offline notes/checklist/status sync with visible conflict handling
2. Service report prints from saved data (browser print)
3. Signoff records timestamp; labeled acknowledgement only
4. Android technician agenda wired to live API

## Backlog by milestone

### M2 — Core CRUD + primary workflow

- [x] Full CRUD customers / locations / work orders
- [x] Dispatch list + overlap detection
- [x] Technician agenda API from assignments
- [x] Status transitions, checklist, notes, time APIs + web views
- [ ] Attachment upload adapter
- [ ] Printable service report
- [ ] Assets write CRUD
- [ ] Android agenda UI

### M3 — AI + Service Memory

- [x] Real Ollama generation path with demo fallback
- [x] Editable AI service report + job prep
- [x] Service Memory search + summarize UI
- [x] Checklist suggestions by job type (confirm-only)

### M4 — Polish

- [ ] Offline sync queue (UUID ops, retry, conflict UI)
- [ ] Signature capture UI
- [ ] Customer job-status link
- [ ] iOS UI layer
- [ ] E2E / scripted demo recording
- [ ] Expanded lint/format/type gates
