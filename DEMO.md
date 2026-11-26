# Field Service — Demo checklist (Milestone 4)

Scripted walkthrough for portfolio demos. Fictional data only. No paid APIs.

## Prerequisites

- [ ] Docker Desktop running
- [ ] From `products/field-service`: `cp .env.example .env` (once)
- [ ] `docker compose up -d`
- [ ] Backend venv + deps installed
- [ ] `alembic upgrade head` && `python -m scripts.seed`
- [ ] API: `uvicorn app.main:app --reload --port 8003`
- [ ] Web: `npm run dev -- --port 3003` (from `web/`)
- [ ] Confirm `GET http://localhost:8003/health` → `"milestone":"4"`

## Credentials

| Role | Email | Password |
| --- | --- | --- |
| Dispatcher | dispatcher@demo.local | demo |
| Technician | tech@demo.local | demo |

## Web demo (≈10 minutes)

### 1. Dashboard polish

1. Open `http://localhost:3003/login`
2. Sign in as **dispatcher@demo.local** / **demo**
3. Confirm cards: jobs today, unassigned, overlap warnings, **completion rate**
4. Use quick links to Work Orders / Reports / Assets

### 2. Dispatch + parts

1. **Work Orders** → create a job (customer + schedule window + technician)
2. If overlap badge appears, note that assignment is allowed with warning (not blocked)
3. Add a note, toggle a checklist item, add 1h time entry
4. Add a part (name → Add part)
5. Click **Printable service report**

### 3. Printable service report + acknowledgement

1. On the report page, confirm customer/location/notes/checklist/labor/parts sections
2. Enter signer name, draw on the canvas (labelled **not a certified e-signature**)
3. Click **Record acknowledgement** — timestamp appears under Customer acknowledgement
4. Click **Print / Save as PDF** (browser print dialog; CSS hides chrome)
5. Cancel print if you do not need a hard copy

### 4. Assets CRUD + history

1. Open **Assets**
2. Create an asset (name, customer, serial/type)
3. Select it → edit maintenance notes → Save
4. Confirm **Service history** panel loads (may be empty for a brand-new asset)
5. Open a seeded asset with history if available

### 5. Customer service history

1. **Customers** → select a seeded customer
2. Confirm locations list + **Service history** jobs

### 6. Labor / parts reports

1. **Reports** → confirm completion %, jobs by status, labor by technician, parts summary
2. Open another printable report from the table

### 7. AI Assist (regression from M3)

1. **AI Assist** → generate service-report draft → edit → approve (status unchanged)
2. Job prep → confirm checklist items
3. Service Memory query `filter` → sources + suggested follow-up

## API smoke (optional)

```bash
# From backend with venv active
curl -s http://localhost:8003/health
TOKEN=$(curl -s -X POST http://localhost:8003/api/v1/auth/demo-login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"dispatcher@demo.local\",\"password\":\"demo\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/reports/service
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8003/api/v1/assignments/agenda?technician_id=<tech-uuid>"
```

## Android (optional)

1. Open `products/field-service/mobile` in Android Studio → Gradle sync (JDK 17)
2. Run `androidApp` on emulator with API up on host `:8003`
3. Agenda shows `source=api` when live; otherwise `source=demo`
4. Tap a job for job detail (live or fallback)

## Quality gates

```bash
cd backend && pytest -q
cd ../web && npm run lint && npm run typecheck
```

## Pass criteria

- [ ] Printable report renders from saved data; browser print works without paid PDF
- [ ] Signoff stores signer + timestamp; UI labels acknowledgement (not certified e-sign)
- [ ] Assets create/update/archive + history views work
- [ ] Reports show labor/parts summaries
- [ ] pytest green; web typecheck/lint green
- [ ] README + this DEMO checklist are current
