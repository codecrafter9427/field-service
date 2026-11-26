# Field Service — MVP Spec

Skeleton-aligned specification for the portfolio MVP. Full production coverage is out of scope for the first vertical slices.

## Purpose

Scheduling, dispatch, and job execution for maintenance, repair, and installation businesses. Web for dispatchers; KMP Android-first mobile for technicians.

## Roles

| Role | Capabilities |
| --- | --- |
| Admin / Dispatcher | Customers, schedule, assignment, reports, settings |
| Technician | Assigned jobs, checklists, notes, parts, signoff |
| Customer (optional) | Read-only job-status link (backlog) |

## Entities (schema)

Organization, User, Customer, ServiceLocation, Asset, WorkOrder (+ `scheduled_start` / `scheduled_end`), WorkOrderAssignment, Checklist, ChecklistItem, JobActivity, TimeEntry, PartUsed, Attachment, CustomerSignoff, AuditEvent.

UUID primary keys, UTC timestamps, organization-scoped rows, archive preferred over hard-delete.

## Work order statuses

Draft → Scheduled → En Route → In Progress → Waiting for Parts → Completed / Cancelled

## API groups

| Group | Prefix | Status |
| --- | --- | --- |
| Auth (demo) | `/api/v1/auth` | Demo login + `/me` (DB-backed, org-scoped) |
| Customers | `/api/v1/customers` | Full CRUD + service history |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Full CRUD + service history |
| Work orders | `/api/v1/work-orders` | Full CRUD + assign + notes + activities |
| Signoffs | `/api/v1/work-orders/{id}/signoffs` | Timestamped acknowledgement (not certified e-sign) |
| Schedule | `/api/v1/schedule` | List with overlap warnings |
| Assignments | `/api/v1/assignments` | Create/list/technicians/agenda |
| Checklists | `/api/v1/checklists` | Create + item patch |
| Time entries | `/api/v1/time-entries` | Create + update |
| Parts used | `/api/v1/parts-used` | List + create |
| Attachments | `/api/v1/attachments` | Coming Soon stub |
| Reports | `/api/v1/reports/service` | Status/labor/parts summary + printable job payload |
| AI service report | `/api/v1/ai/service-report` | Draft + approve (human edit required) |
| AI job prep | `/api/v1/ai/job-prep` | History summary + confirm checklist |
| AI Service Memory | `/api/v1/ai/service-memory` | Recurring-failure search + summarize |
| Health | `/health` | Milestone 4 |

Shared conventions: REST JSON, pagination/search/sort on lists, error shape `{error:{code,message,details}}`, tenant authorization on every business endpoint.

Overlap rule: when assigning or creating with a technician and both jobs have `scheduled_start`/`scheduled_end`, the API **warns** (`overlap_warning` + overlapping IDs) if intervals overlap for the same technician. Cancelled jobs are excluded. Assignment is not blocked.

## Web baseline

**M2:** dashboard snapshot, customer + location directory, work-order create/assign/status, notes/checklist/time panels, schedule list with overlap badges.

**M3:** AI Assist page — service report draft/approve, job prep + checklist confirm, Service Memory search UI; assets read list.

**M4:** printable service report (browser print CSS), acknowledgement signature stub, assets CRUD + history, labor/parts reports, dispatcher UX polish (parts on jobs, completion rate).

## Mobile baseline

- Technician agenda + job detail API clients (`ApiClient` / `AgendaRepository`)
- Android UI: agenda list → job detail; live API with demo fallback
- Android Studio sync documented; device run optional
- Offline drafts / certified e-sign → backlog

## AI (M3)

- Structured editable service report from notes/transcript
- Job prep summary from asset history/checklist
- Checklist suggestions by job type (technician confirms)
- Rules: backend-only; DemoAIProvider if Ollama absent; never complete job / certify safety / sign for customer
- Optional Ollama adapter with demo fallback

## Differentiator — Service Memory

Search recurring failures by asset/customer. AI summarizes repeated issues and suggests maintenance follow-up from **recorded history** only. Show sources; require human confirmation before creating follow-up work. Seeded job history includes filter/leak themes for demos.

## Acceptance criteria

### Milestone 1–3 (done)

See README milestone checklists.

### Milestone 4 (done when)

1. Printable service report from saved data via browser print (no paid PDF API)
2. Acknowledgement capture UI labeled not certified e-sign; signoff API stores timestamp
3. Assets write CRUD + service history by customer/asset
4. Labor/parts summary reports
5. Lint/typecheck + expanded pytest green
6. README + DEMO.md scripted checklist
7. KMP agenda/job detail clients polished; Android Studio sync documented

### Remaining backlog

1. Offline notes/checklist/status sync with visible conflict handling
2. Customer read-only job-status link
3. iOS UI layer
4. Attachment binary upload adapter

## Backlog by milestone

### M2 — Core CRUD + primary workflow

- [x] Full CRUD customers / locations / work orders
- [x] Dispatch list + overlap detection
- [x] Technician agenda API from assignments
- [x] Status transitions, checklist, notes, time APIs + web views
- [x] Printable service report (delivered in M4)
- [x] Assets write CRUD (delivered in M4)
- [ ] Attachment upload adapter

### M3 — AI + Service Memory

- [x] Real Ollama generation path with demo fallback
- [x] Editable AI service report + job prep
- [x] Service Memory search + summarize UI
- [x] Checklist suggestions by job type (confirm-only)

### M4 — Polish

- [x] Signature capture UI (acknowledgement label)
- [x] Printable service-report polish
- [x] Assets CRUD + history + labor/parts reports
- [x] E2E / scripted demo checklist (`DEMO.md`)
- [x] Expanded lint/format/type gates
- [x] Android agenda/job detail API clients + Studio sync docs
- [ ] Offline sync queue (UUID ops, retry, conflict UI)
- [ ] Customer job-status link
- [ ] iOS UI layer
