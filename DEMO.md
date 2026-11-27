# Field Service — Demo checklist (Milestone 6)

Scripted walkthrough for portfolio demos. Fictional data only. No paid APIs.

## Prerequisites

- [ ] Docker Desktop running
- [ ] From `products/field-service`: `cp .env.example .env` (once)
- [ ] `docker compose up -d`
- [ ] Backend venv + deps installed
- [ ] `alembic upgrade head` && `python -m scripts.seed`
- [ ] API: `uvicorn app.main:app --reload --port 8003`
- [ ] Web: `npm run dev -- --port 3003` (from `web/`)
- [ ] Confirm `GET http://localhost:8003/health` → `"milestone":"6"`

## Credentials

| Role | Email | Password |
| --- | --- | --- |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |

## Web demo (≈12 minutes)

### 1. Customer job-status portal (M6)

1. Open (no login): `http://localhost:3003/status/demo-portal-status-token-m6-northwind`
2. Confirm status, schedule, customer/location, service summary — **no internal notes or rates**
3. Login as **dispatcher@demo.local** → **Work Orders** → select a job
4. Under **Customer status link** → **Create & copy link** → open the copied URL in a private window
5. Click **Revoke** → refresh the status URL → link no longer works
6. Optional: login as technician → confirm create link fails (403)

### 2. Dashboard polish

1. Open `http://localhost:3003/login`
2. Sign in as **dispatcher@demo.local** / **demo**
3. Confirm cards: jobs today, unassigned, overlap warnings, **completion rate**
4. Use quick links to Work Orders / Reports / Assets

### 3. Dispatch + parts

1. **Work Orders** → create a job (customer + schedule window + technician)
2. If overlap badge appears, note that assignment is allowed with warning (not blocked)
3. Add a note, toggle a checklist item, add 1h time entry
4. Add a part (name → Add part)
5. Click **Printable service report**

### 4. Printable service report + acknowledgement

1. On the report page, confirm customer/location/notes/checklist/labor/parts sections
2. Enter signer name, draw on the canvas (labelled **not a certified e-signature**)
3. Click **Record acknowledgement** — timestamp appears under Customer acknowledgement
4. Click **Print / Save as PDF** (browser print dialog; CSS hides chrome)

### 5. Assets + reports + AI (regression)

1. **Assets** CRUD + service history
2. **Reports** → completion %, jobs by status, labor, parts
3. **AI Assist** → service-report draft/approve, job prep, Service Memory `filter`

## Insights connector smoke (M6)

```bash
TOKEN=$(curl -s -X POST http://localhost:8003/api/v1/auth/demo-login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"dispatcher@demo.local\",\"password\":\"demo\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/connectors/insights/v1/health
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/connectors/insights/v1/summary
```

See [`CONNECTORS.md`](CONNECTORS.md).

## Android — offline sync (Milestone 5 regression)

1. Open `products/field-service/mobile` in Android Studio → Gradle sync (JDK 17)
2. Run `androidApp` on emulator with API up on host `:8003`
3. **Airplane mode ON** → queue note + checklist + status → badges **Pending**
4. **Airplane mode OFF** → **Drain queue** → web reflects changes
5. **Conflict demo:** stale status → **Conflict** → Keep local / Take server

Note: login tokens are opaque signed strings (`fs1.…`); do not parse them on device.

## Quality gates

```bash
cd backend && pytest -q
cd ../web && npm run lint && npm run typecheck
```

## Pass criteria

- [ ] Customer status page works for seeded + newly created links; revoke/expiry deny access
- [ ] Redacted payload: no notes/rates; tech cannot manage portal links
- [ ] Insights connector health + summary return for dispatcher
- [ ] Offline note + checklist + status queue → reconnect drain succeeds (M5)
- [ ] Conflict UI on stale status/checklist; pytest green including `test_m5_offline_sync.py`
- [ ] README + this DEMO checklist are current (milestone 6)
