# Infrastructure

Shared infrastructure (Postgres, Redis, etc).

## Compose integration notes

- The order API and Celery worker run as separate services:
	- `order` runs `python app.py` on port 7000.
	- `order_worker` runs `celery -A celery_worker.celery_app worker --loglevel=info`.
- Core app services (`user`, `product`, `chat`, `order`, `order_worker`) wait for healthy `db` and `redis` dependencies.
- Infrastructure health checks:
	- Postgres: `pg_isready`
	- Redis: `redis-cli ping`

## Compose smoke workflow

Run a one-command integration smoke check from repo root:

```sh
./scripts/compose_smoke.sh
```

What it validates:
- Compose startup for db, redis, user, product, chat, order, and order_worker
- Protected user endpoint flow (register -> JWT obtain -> profile)
- Protected product GraphQL flow using service JWT
- Protected order create/read flow using service JWT
- Chat WebSocket connect and join-room handshake

Optional behavior:
- Keep services running after checks: `SMOKE_KEEP_UP=1 ./scripts/compose_smoke.sh`