# Field Service — MVP Spec

Skeleton-aligned specification for the portfolio MVP. Full production coverage is out of scope for the first vertical slice.

## Purpose

Scheduling, dispatch, and job execution for maintenance, repair, and installation businesses. Web for dispatchers; KMP Android-first mobile for technicians.

## Roles

| Role | Capabilities |
| --- | --- |
| Admin / Dispatcher | Customers, schedule, assignment, reports, settings |
| Technician | Assigned jobs, checklists, notes, parts, signoff |
| Customer (optional) | Read-only job-status link (backlog M4) |

## Entities (implemented in M1 schema)

Organization, User, Customer, ServiceLocation, Asset, WorkOrder, WorkOrderAssignment, Checklist, ChecklistItem, JobActivity, TimeEntry, PartUsed, Attachment, CustomerSignoff, AuditEvent.

UUID primary keys, UTC timestamps, organization-scoped rows, archive preferred over hard-delete.

## Work order statuses

Draft → Scheduled → En Route → In Progress → Waiting for Parts → Completed / Cancelled

## API groups

| Group | Prefix | Status |
| --- | --- | --- |
| Auth (demo) | `/api/v1/auth` | Demo login + `/me` (DB-backed, org-scoped) |
| Customers | `/api/v1/customers` | M1 org-scoped list; full CRUD → M2 |
| Service locations | `/api/v1/service-locations` | Coming Soon stub |
| Assets | `/api/v1/assets` | Coming Soon stub |
| Work orders | `/api/v1/work-orders` | M1 org-scoped list; full CRUD → M2 |
| Schedule | `/api/v1/schedule` | Coming Soon stub |
| Assignments | `/api/v1/assignments` | Coming Soon stub |
| Checklists | `/api/v1/checklists` | Coming Soon stub |
| Time entries | `/api/v1/time-entries` | Coming Soon stub |
| Parts used | `/api/v1/parts-used` | Coming Soon stub |
| Attachments | `/api/v1/attachments` | Coming Soon stub |
| Reports | `/api/v1/reports/service` | Coming Soon stub |
| AI service report | `/api/v1/ai/service-report` | Provider stub |
| AI job prep | `/api/v1/ai/job-prep` | Provider stub |
| Health | `/health` | Implemented |

Shared conventions: REST JSON, pagination/search/sort on lists, error shape `{error:{code,message,details}}`, tenant authorization on every business endpoint.

## Web baseline (target)

- Dashboard: jobs today, unassigned/overdue, completion rate
- Customer + service-location directory
- Work orders with checklist, parts, labor, attachments metadata
- Calendar / dispatch board with overlap warnings
- Asset register + service history
- Estimate/quote fields; printable browser service report
- Reports by status/technician

**M1:** demo login works; customers/work-orders list APIs org-scoped; UI feature routes still Coming Soon until M2.

## Mobile baseline (target)

- Technician agenda and assigned jobs
- Status transitions; checklist; notes; time tracking
- Local photo capture; voice note with platform speech fallback
- Customer signature as acknowledgement (not certified e-sign)
- Offline drafts with conflict-aware sync

**M1:** KMP shell only — mobile run can wait.

## AI (target)

- Structured editable service report from notes/transcript
- Job prep summary from asset history/checklist
- Checklist suggestions by job type (technician confirms)
- Rules: backend-only; DemoAIProvider if Ollama absent; never complete job / certify safety / sign for customer

## Differentiator — Service Memory

Search recurring failures by asset/customer. AI summarizes repeated issues and suggests maintenance follow-up from **recorded history** only. Show sources; require human confirmation before creating follow-up work. Seeded job history supports later demos (M3).

## Acceptance criteria

### Milestone 1 (done when)

1. Local Postgres via Docker Compose; `.env.example` documented
2. Alembic migrations apply cleanly
3. Seed creates ≥12 customers, 15 assets, 20 jobs, 5 technicians + history
4. Demo login works for ≥2 roles; tokens are org-scoped
5. `/health` OK; auth + tenant smoke tests pass
6. No paid APIs required

### Full MVP vertical slice (later milestones)

1. Dispatcher-created job appears in technician agenda (same backend)
2. Offline notes/checklist/status sync with visible conflict handling
3. Schedule warns on overlapping assignments
4. Service report prints from saved data (browser print)
5. Signoff records timestamp; labeled acknowledgement only
6. AI report is edited/approved before final attachment
7. Service Memory visible with sources
8. DemoAIProvider always works; Ollama optional

## Backlog by milestone

### M2 — Core CRUD + primary workflow

- [ ] Full CRUD customers / locations / assets / work orders
- [ ] Dispatch board + overlap detection
- [ ] Technician agenda (web + Android) from assignments
- [ ] Status transitions, checklist, notes, time, parts APIs
- [ ] Attachment upload adapter
- [ ] Printable service report

### M3 — AI + Service Memory

- [ ] Real Ollama generation path beyond stub
- [ ] Editable AI service report + job prep
- [ ] Service Memory search + summarize UI
- [ ] Checklist suggestions by job type (confirm-only)

### M4 — Polish

- [ ] Offline sync queue (UUID ops, retry, conflict UI)
- [ ] Signature capture UI
- [ ] Customer job-status link
- [ ] iOS UI layer
- [ ] E2E / scripted demo recording
- [ ] Expanded lint/format/type gates
