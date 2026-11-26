# Field Service — MVP Spec

Skeleton-aligned specification for the portfolio MVP. Full production coverage is out of scope for the first vertical slice.

## Purpose

Scheduling, dispatch, and job execution for maintenance, repair, and installation businesses. Web for dispatchers; KMP Android-first mobile for technicians.

## Roles

| Role | Capabilities |
| --- | --- |
| Admin / Dispatcher | Customers, schedule, assignment, reports, settings |
| Technician | Assigned jobs, checklists, notes, parts, signoff |
| Customer (optional) | Read-only job-status link (backlog) |

## Entities (planned)

Organization, User, Customer, ServiceLocation, Asset, WorkOrder, WorkOrderAssignment, Checklist, ChecklistItem, JobActivity, TimeEntry, PartUsed, Attachment, CustomerSignoff, AuditEvent.

UUID primary keys, UTC timestamps, organization-scoped rows, archive preferred over hard-delete.

## Work order statuses

Draft → Scheduled → En Route → In Progress → Waiting for Parts → Completed / Cancelled

## API groups

| Group | Prefix | Skeleton status |
| --- | --- | --- |
| Auth (demo) | `/api/v1/auth` | Placeholder login |
| Customers | `/api/v1/customers` | Coming Soon stub |
| Service locations | `/api/v1/service-locations` | Coming Soon stub |
| Assets | `/api/v1/assets` | Coming Soon stub |
| Work orders | `/api/v1/work-orders` | Coming Soon stub |
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

Shared conventions: REST JSON, pagination/search/sort on lists, error shape `{error:{code,message,details}}`, tenant authorization on every business endpoint (to be enforced when CRUD lands).

## Web baseline (target)

- Dashboard: jobs today, unassigned/overdue, completion rate
- Customer + service-location directory
- Work orders with checklist, parts, labor, attachments metadata
- Calendar / dispatch board with overlap warnings
- Asset register + service history
- Estimate/quote fields; printable browser service report
- Reports by status/technician

**Skeleton:** demo login + Coming Soon for customers, work orders, schedule, assets, reports.

## Mobile baseline (target)

- Technician agenda and assigned jobs
- Status transitions; checklist; notes; time tracking
- Local photo capture; voice note with platform speech fallback
- Customer signature as acknowledgement (not certified e-sign)
- Offline drafts with conflict-aware sync

**Skeleton:** KMP shared agenda stubs + Android app shell. No offline/signature/AI yet.

## AI (target)

- Structured editable service report from notes/transcript
- Job prep summary from asset history/checklist
- Checklist suggestions by job type (technician confirms)
- Rules: backend-only; DemoAIProvider if Ollama absent; never complete job / certify safety / sign for customer

## Differentiator — Service Memory

Search recurring failures by asset/customer. AI summarizes repeated issues and suggests maintenance follow-up from **recorded history** only. Show sources; require human confirmation before creating follow-up work. Not implemented in this scaffold (backlog + stub endpoint reserved).

## Acceptance criteria (MVP vertical slice — when implemented)

1. Dispatcher-created job appears in technician agenda (same backend)
2. Offline notes/checklist/status sync with visible conflict handling
3. Schedule warns on overlapping assignments
4. Service report prints from saved data (browser print)
5. Signoff records timestamp; labeled acknowledgement only
6. AI report is edited/approved before final attachment
7. Demo login works; seed includes ~12 customers, 15 assets, 20 jobs, 5 technicians
8. No paid APIs required; Ollama optional; DemoAIProvider always works

## Backlog (explicitly not in scaffold)

- [ ] SQLAlchemy models + Alembic migrations
- [ ] Seed script with fictional demo dataset
- [ ] Full CRUD + tenant auth tests
- [ ] Dispatch board + overlap detection
- [ ] Offline sync queue (UUID ops, retry, conflict UI)
- [ ] Signature capture UI
- [ ] Attachment upload adapter
- [ ] Real Ollama generation path beyond stub
- [ ] Service Memory search + summarize UI
- [ ] Printable service report
- [ ] iOS UI layer
- [ ] Customer job-status link
- [ ] E2E / scripted demo
