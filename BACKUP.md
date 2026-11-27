# Field Service — Backup & restore

Portfolio demo guidance for the local Postgres volume (Docker Compose host port **5434**).

## Dump

With Compose running from `products/field-service`:

```bash
docker compose exec -T db pg_dump -U field_service -d field_service -Fc > field_service_backup.dump
```

Plain SQL alternative:

```bash
docker compose exec -T db pg_dump -U field_service -d field_service > field_service_backup.sql
```

## Restore

```bash
# Custom format
docker compose exec -T db pg_restore -U field_service -d field_service --clean --if-exists < field_service_backup.dump

# Or SQL
docker compose exec -T db psql -U field_service -d field_service < field_service_backup.sql
```

After restore, re-run migrations only if the dump is older than `alembic` head:

```bash
cd backend
alembic upgrade head
```

## Notes

- Default credentials are local placeholders from `.env.example` — not production secrets.
- Volume name: `field_service_pgdata` (see `docker-compose.yml`).
- Customer portal **raw tokens are never stored**; only SHA-256 hashes. Restoring a DB does not recover previously shared raw links unless you kept them outside the DB.
- This is a prototype backup path — not a HA / PITR runbook.
