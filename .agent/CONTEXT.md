# CONTEXT.md — Current Project State

## Last Updated
**Date:** 2026-03-29
**Session summary:** Verified live docker backend startup from clean state, passed smoke checks end-to-end, and confirmed healthy running services.

---

## Current Sprint Focus
**Goal:** Begin Milestone 12 observability and security hardening across services.
**Deadline:** N/A
**Priority order:**
1. Milestone 12 observability and rate-limiting tasks
2. Milestone 12 caching tasks
3. Cross-service instrumentation consistency

---

## What Has Been Completed
- M11-U1 — Integrated persistent database for user service
- `.agent/` required knowledge base files initialized and populated
- M11-U2 — Refactored user service to enforce modular service-layer architecture
- M11-U3 — Added explicit validation and structured validation error responses for user endpoints
- M11-U4 — Optimized feed/follow query paths to avoid N+1 patterns
- M11 cross-service productionization for product/chat/order services

---

## What Is In Progress
- Post-M12 read-path performance hardening follow-ups

---

## What Is Blocked
- None

---

## Recently Modified Files
- services/common/cache_service.py
- services/common/test_cache_service.py
- docker-compose.yml
- services/order/Dockerfile
- services/user/Dockerfile
- services/product/Dockerfile
- services/chat/Dockerfile
- infrastructure/README.md
- scripts/compose_smoke.sh
- services/chat/app.py
- services/chat/service.py
- services/product/app.py
- services/product/test_product.py
- services/chat/test_chat.py
- services/common/test_cache_service.py
- services/order/app.py
- services/order/test_order.py
- services/common/rate_limit.py
- .agent/CONTEXT.md
- .agent/TASKS.md
- .agent/CHANGELOG.md
- .agent/IMPROVEMENTS.md
- .agent/DECISIONS.md
- services/product/service.py
- services/product/schema.py
- services/product/test_product.py
- services/product/app.py
- services/chat/app.py
- services/chat/service.py
- services/chat/test_chat.py
- services/order/app.py
- services/order/service.py
- services/order/models.py
- services/order/celery_worker.py
- services/order/test_order.py
- services/common/logging_service.py
- services/common/__init__.py
- services/user/userservice/middleware.py
- services/user/userservice/rate_limit_middleware.py
- services/user/userservice/settings.py
- services/user/accounts/tests.py
- services/user/accounts/views.py

---

## Known Issues & Risks
- Product, chat, and order services still have pending persistent DB and modularization tasks.
- Explicit validation, caching, and observability are not fully implemented across all services.

---

## Environment State
- [x] Multi-service repository structure established
- [x] docker-compose infrastructure present
- [x] Inter-service JWT auth model defined
- [ ] All services productionized per milestone 11/12 criteria

---

## Notes
- Use AGENT_CONTEXT.md and DEVELOPMENT_ROADMAP.md as canonical input for milestone progress.
- Inter-service auth constraints in SECURITY.md are non-negotiable.
- Test execution in host shell requires `POSTGRES_HOST=localhost` when not running inside compose network.
- Query-count regression tests for user service are now present in `accounts/tests.py`.
- Product test suite now includes auth boundary and seeded DB-backed GraphQL behavior checks.
- Product tests now also validate missing GraphQL query payload and invalid search category input handling.
- Product service now fails fast on weak/missing `SERVICE_JWT_SECRET` and returns generic invalid-token errors.
- Chat service now centralizes validation/persistence logic in `service.py` and enforces stricter payload checks.
- Order service now centralizes auth/payload/data operations in `service.py` and enforces strict payload validation on create/status routes.
- Order worker now supports environment-driven Celery broker/backend config with explicit regression test coverage.
- Consolidated cross-service test status: product 9 passed, chat 4 passed/2 skipped (server-dependent), order 8 passed.
- Structured logging baseline implemented for product/chat/order with queue-based JSON output and request/connection context.
- User service now emits structured request lifecycle and exception logs via shared middleware.
- Shared rate-limiter baseline implemented with Redis-aware utility and local fallback.
- Product GraphQL and order write/process endpoints now enforce configurable per-window limits.
- Chat runtime now rate-limits high-volume `message` actions per room/connection key.
- User service now enforces rate limits on auth and sensitive social endpoints via middleware.
- Consolidated cross-service test status after rate-limiting slice: product 10 passed, chat 5 passed/2 skipped, order 9 passed, user 16 passed.
- Shared cache utility now provides Redis-backed (or fallback memory) JSON caching primitives.
- Product GraphQL read responses now use cache with hit/miss headers for observability.
- User feed responses now use cache with write-path invalidation on key social mutations.
- Consolidated test status after caching slice: product 11 passed, user 18 passed.
- Order read endpoint now uses cache with explicit invalidation on create/status updates.
- Consolidated test status after order caching increment: order 11 passed.
- Chat history reads now use shared cache with invalidation on persisted message writes.
- Chat test suite status after caching increment: 8 passed, 2 skipped, warning-free.
- Shared cache utility now supports `delete_prefix` for grouped invalidation patterns.
- Added direct unit coverage for prefix deletion behavior in `services/common/test_cache_service.py`.
- Prefix invalidation now emits structured debug metrics (`cache_prefix`, deleted key counts, `duration_ms`).
- Prefix invalidation debug metrics now support env-configurable enable/disable and sample-rate controls.
- Docker compose now includes a dedicated `order_worker` service and health-gated startup dependencies.
- Compose environment now pins internal service connectivity via `POSTGRES_HOST=db` and `REDIS_URL=redis://redis:6379/0`.
- All service images now build from the shared `services/` context so the shared `common` package is available in containers.
- Compose smoke script now completes end-to-end, including protected checks for user/product/order and authenticated chat join validation.
- Chat WebSocket handler now supports websockets 16 request object shape and Authorization-header JWT fallback.
- Product readiness now uses explicit `/healthz` probe instead of ambiguous GraphQL GET behavior.
- Latest live verification status: `SMOKE_KEEP_UP=1 ./scripts/compose_smoke.sh` passed, and `docker compose ps` shows healthy user/product/order/chat/db/redis with running order worker.
