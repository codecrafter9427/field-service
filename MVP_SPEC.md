# Field Service — MVP Spec

Skeleton-aligned specification for the portfolio MVP. Full production coverage is out of scope for the first vertical slices.

## Purpose

Scheduling, dispatch, and job execution for maintenance, repair, and installation businesses. Web for dispatchers; KMP Android-first mobile for technicians.

## Roles

| Role | Capabilities |
| --- | --- |
| Admin / Dispatcher | Customers, schedule, assignment, reports, settings, **customer portal links** |
| Technician | Assigned jobs, checklists, notes, parts, signoff |
| Customer (link) | Read-only job-status via expiring/revocable token |

## Entities (schema)

Organization, User, Customer, ServiceLocation, Asset, WorkOrder (+ `scheduled_start` / `scheduled_end`), WorkOrderAssignment, Checklist, ChecklistItem, JobActivity, TimeEntry, PartUsed, Attachment, CustomerSignoff, AuditEvent, **CustomerPortalLink**.

UUID primary keys, UTC timestamps, organization-scoped rows, archive preferred over hard-delete.

## Work order statuses

Draft → Scheduled → En Route → In Progress → Waiting for Parts → Completed / Cancelled

## API groups

| Group | Prefix | Status |
| --- | --- | --- |
| Auth (demo) | `/api/v1/auth` | Signed HMAC login + `/me` (DB-backed, org-scoped) |
| Customers | `/api/v1/customers` | Full CRUD + service history |
| Service locations | `/api/v1/service-locations` | Full CRUD |
| Assets | `/api/v1/assets` | Full CRUD + service history |
| Work orders | `/api/v1/work-orders` | Full CRUD + assign + notes + activities |
| Portal | `/api/v1/work-orders/{id}/portal-links`, `/portal-links/{id}/revoke`, `/public/job-status` | M6 |
| Signoffs | `/api/v1/work-orders/{id}/signoffs` | Timestamped acknowledgement (not certified e-sign) |
| Schedule | `/api/v1/schedule` | List with overlap warnings |
| Assignments | `/api/v1/assignments` | Create/list/technicians/agenda |
| Checklists | `/api/v1/checklists` | Create + item patch |
| Time entries | `/api/v1/time-entries` | Create + update |
| Parts used | `/api/v1/parts-used` | List + create |
| Attachments | `/api/v1/attachments` | Coming Soon stub |
| Reports | `/api/v1/reports/service` | Status/labor/parts summary + printable job payload |
| Insights connector | `/api/v1/connectors/insights/v1` | Read-only aggregates for Business Insights |
| AI service report | `/api/v1/ai/service-report` | Draft + approve (human edit required) |
| AI job prep | `/api/v1/ai/job-prep` | History summary + confirm checklist |
| AI Service Memory | `/api/v1/ai/service-memory` | Recurring-failure search + summarize |
| Health | `/health` | Milestone 6 |

Shared conventions: REST JSON, pagination/search/sort on lists, error shape `{error:{code,message,details}}`, tenant authorization on every business endpoint.

**M5 sync contract:** notes accept optional `client_operation_id` (idempotent per org); status PATCH requires `base_updated_at`; checklist item PATCH requires `base_updated_at`. Stale base → `409` with `{error:{code:"conflict", details:{server}}}`.

**M6 portal:** tokens hashed at rest (SHA-256); raw shown once; public payload allowlists status/schedule/summary/checklist progress/parts names+qty/ack flag — never internal notes, rates, tech private data, or other jobs.

Overlap rule: when assigning or creating with a technician and both jobs have `scheduled_start`/`scheduled_end`, the API **warns** (`overlap_warning` + overlapping IDs) if intervals overlap for the same technician. Cancelled jobs are excluded. Assignment is not blocked.

## Web baseline

**M2–M5:** dashboard, customers, work orders, schedule, AI Assist, printable report, assets, reports, offline mobile.

**M6:** public `/status/[token]`; dispatcher **Customer status link** create/copy/revoke on work-order detail.

## Mobile baseline

- Technician agenda + job detail API clients
- **M5:** offline UUID op queue for notes, checklist, status; conflict UI
- **M6:** access token opaque (format changed to signed `fs1.…`); no queue contract changes
- Attachments / signoff / time offline + certified e-sign → backlog

## AI (M3)

- Structured editable service report from notes/transcript
- Job prep summary from asset history/checklist
- Checklist suggestions by job type (technician confirms)
- Rules: backend-only; DemoAIProvider if Ollama absent; never complete job / certify safety / sign for customer

## Differentiator — Service Memory

Search recurring failures by asset/customer. AI summarizes repeated issues and suggests maintenance follow-up from **recorded history** only.

## Acceptance criteria

### Milestone 1–5 (done)

See README milestone checklists.

### Milestone 6 (done when)

1. Dispatcher creates portal link → customer opens `/status/{token}` → sees status + schedule + safe summary only
2. Expired or revoked token unusable; pytest covers both
3. Token scoped to one job; no notes/rates/other-customer leak; tech cannot create/revoke
4. Staff Bearer expires per `ACCESS_TOKEN_EXPIRE_MINUTES`; login + portal rate-limited
5. Insights connector returns completion rate, jobs by status, labor/parts; `CONNECTORS.md` present
6. `BACKUP.md` + CI; `/health` → milestone `6`; M5 offline pytest still green; no paid APIs

### Remaining backlog

1. iOS UI layer
2. Attachment binary upload adapter
3. Offline attachments / signoff / time

## Backlog by milestone

### M5 — Offline sync

- [x] Offline sync queue (UUID ops, retry, conflict UI) for notes/checklist/status
- [x] Customer job-status link (delivered in M6)
- [ ] iOS UI layer

### M6 — Portal + hardening + Insights

- [x] Customer portal links + public redacted status
- [x] Signed staff tokens, rate limits, role gates, audit
- [x] Insights connector + docs/CI/backup
