# Field Service — Insights connector (v1)

Read-only HTTP contract for **Business Insights** to pull org-scoped field ops aggregates. No writes. No sibling DB coupling.

## Base URL

```
http://localhost:8003/api/v1/connectors/insights/v1
```

## Auth

1. **Staff Bearer** (required): `Authorization: Bearer <access_token>` from `POST /api/v1/auth/demo-login`  
   Roles: `admin` or `dispatcher` only (`technician` → 403).
2. **Optional connector key**: if `INSIGHTS_CONNECTOR_KEY` is set in the Field Service env, every connector request must also send  
   `X-Connector-Key: <same value>`.

Tokens are HMAC-signed staff access tokens (opaque to clients). Expiry: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480).

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness + product/connector version |
| GET | `/summary` | Full aggregate (preferred sync payload) |
| GET | `/jobs-by-status` | Status histogram |
| GET | `/completion` | Completion rate |
| GET | `/labor` | Labor by technician |
| GET | `/parts` | Parts totals |

### `GET /health`

```json
{
  "status": "ok",
  "product": "field-service",
  "connector": "insights",
  "version": "v1",
  "milestone": "6"
}
```

### `GET /summary`

```json
{
  "source_product": "field-service",
  "connector_version": "v1",
  "organization_id": "<uuid>",
  "jobs_by_status": [{ "status": "completed", "count": 5 }],
  "total_jobs": 20,
  "completed_jobs": 5,
  "completion_rate": 25.0,
  "labor": [{
    "technician_id": "<uuid>",
    "technician_name": "Tech One",
    "total_minutes": 480,
    "entry_count": 12
  }],
  "total_labor_minutes": 1200,
  "parts": [{
    "part_name": "HEPA Filter",
    "total_quantity": "4.00",
    "total_cost": "120.00"
  }],
  "parts_total_cost": "120.00",
  "generated_at": "2026-11-27T18:00:00Z"
}
```

Math matches `GET /api/v1/reports/service` (shared builder).

## Errors

Shared envelope: `{ "error": { "code", "message", "details" } }` via FastAPI `detail`.  
Common: `401` unauthorized / bad connector key, `403` role, `429` rate limited (login/portal; connector uses staff auth).

## Stability

Additive fields only within `v1`. Breaking changes → `v2`.

## Out of scope

Customer PII dumps, job notes, printable report bodies, AI endpoints, portal tokens, mutations.
