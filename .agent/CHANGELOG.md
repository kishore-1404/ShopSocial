# CHANGELOG.md — Agent Change Log

> Newest entries first.

### [2026-03-29] — Runtime verification: live docker backend spin-up

**Task:** TASK-014 — Live docker runtime verification
**Triggered by:** User request to verify docker can actually spin and backend works

**Changes:**
- Verification run only (no application code mutation)

**Tests/Validation:**
- `docker compose down --remove-orphans` — clean reset
- `SMOKE_KEEP_UP=1 ./scripts/compose_smoke.sh` — passed
- `docker compose ps` — user/product/order/chat/db/redis healthy; order worker running

**Breaking changes:** No

### [2026-03-29] — Integration reliability: deterministic product readiness endpoint

**Task:** TASK-013 — Product deterministic readiness endpoint
**Triggered by:** Continue after TASK-012 completion

**Changes:**
- `services/product/app.py` — added unauthenticated `/healthz` endpoint returning service health payload
- `services/product/test_product.py` — added unit test for `/healthz` response contract
- `docker-compose.yml` — changed product healthcheck to HTTP probe against `/healthz`
- `scripts/compose_smoke.sh` — changed product readiness wait target from `/graphql` to `/healthz`

**Tests/Validation:**
- `SMOKE_KEEP_UP=0 ./scripts/compose_smoke.sh` — passed (product readiness now `HTTP 200`)

**Breaking changes:** No

### [2026-03-29] — Integration automation: compose smoke workflow and runtime compatibility fixes

**Task:** TASK-012 — Compose smoke integration workflow
**Triggered by:** Continue after docker integration hardening; user reported smoke wait/hang

**Changes:**
- `scripts/compose_smoke.sh` — added one-command compose smoke workflow with startup checks, protected API verifications, authenticated chat join probe, and failure diagnostics
- `docker-compose.yml` — switched service builds to shared `services/` context, propagated runtime `SERVICE_JWT_SECRET`, and retained integration wiring improvements
- `services/user/Dockerfile`, `services/product/Dockerfile`, `services/chat/Dockerfile`, `services/order/Dockerfile` — updated copy paths to support shared-context image builds with `common` module inclusion
- `services/chat/app.py` — added websockets 16-compatible handler/header access and JWT fallback via Authorization header
- `services/chat/service.py` — added Authorization header JWT extractor
- `services/chat/test_chat.py` — added extraction coverage for Authorization header JWT format

**Tests/Validation:**
- `SMOKE_KEEP_UP=0 ./scripts/compose_smoke.sh` — passed (all smoke checks)

**Breaking changes:** No

### [2026-03-29] — Docker and integration hardening: compose role split and health-gated startup

**Task:** TASK-011 — Docker compose integration hardening
**Triggered by:** User request to work on docker and integration

**Changes:**
- `docker-compose.yml` — split order API and worker into separate services, added health checks, health-gated dependencies, and explicit internal host/broker overrides
- `services/order/Dockerfile` — aligned default container command to start the order API (`python app.py`)
- `infrastructure/README.md` — documented compose integration topology and health-check behavior

**Tests/Validation:**
- `docker compose config` — passed

**Breaking changes:** No

### [2026-03-29] — Continue post-M12 hardening: cache invalidation debug sampling controls

**Task:** TASK-010 — Cache debug sampling controls
**Triggered by:** Continue after prefix metrics instrumentation

**Changes:**
- `services/common/cache_service.py` — added env-configurable toggle and sample-rate guard for prefix invalidation debug metrics
- `services/common/test_cache_service.py` — expanded deterministic tests for enabled/disabled/sampled debug emission behavior

**Tests:**
- `pytest -q services/common/test_cache_service.py` — passed (5)
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (8), skipped (2)

**Breaking changes:** No

### [2026-03-28] — Continue post-M12 hardening: cache prefix metrics instrumentation

**Task:** TASK-009 — Cache prefix metrics instrumentation
**Triggered by:** Continue after prefix invalidation rollout

**Changes:**
- `services/common/cache_service.py` — added structured debug metrics on prefix invalidation (`cache_prefix`, redis/memory deleted counts, duration)
- `services/common/test_cache_service.py` — added unit test validating debug metric emission

**Tests:**
- `pytest -q services/common/test_cache_service.py` — passed (2)
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (8), skipped (2)

**Breaking changes:** No

### [2026-03-28] — Continue post-M12 hardening: chat prefix-cache invalidation

**Task:** TASK-008 — Chat prefix cache invalidation
**Triggered by:** Continue after chat history caching rollout

**Changes:**
- `services/common/cache_service.py` — added `delete_prefix` support for grouped cache invalidation (Redis + memory fallback)
- `services/chat/service.py` — switched chat history invalidation to room-level prefix invalidation
- `services/chat/test_chat.py` — updated cache invalidation test to assert prefix invalidation behavior
- `services/common/test_cache_service.py` — added unit test for memory fallback prefix deletion behavior

**Tests:**
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (8), skipped (2)
- `pytest -q services/common/test_cache_service.py` — passed (1)

**Breaking changes:** No

### [2026-03-28] — Continue post-M12 hardening: chat history caching extension

**Task:** TASK-007 — Chat history caching expansion
**Triggered by:** Continue after order read caching increment

**Changes:**
- `services/chat/service.py` — added cache key helper, history cache read/write behavior, and invalidation on message persistence
- `services/chat/app.py` — wired shared cache client into join/history flows and message-write invalidation path
- `services/chat/test_chat.py` — added cache hit/miss/invalidation unit tests and updated datetime usage to remove deprecation warnings

**Tests:**
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (8), skipped (2)

**Breaking changes:** No

### [2026-03-28] — Continue post-M12 hardening: order read caching extension

**Task:** TASK-006 — Order read caching expansion
**Triggered by:** Continue after TASK-005 completion

**Changes:**
- `services/order/app.py` — added order read caching with `X-Cache` hit/miss headers and write-path invalidation on create/status updates
- `services/order/test_order.py` — added cache hit and cache invalidation regression tests; integrated shared cache reset in fixtures

**Tests:**
- `pytest -q` in `services/order` (with `POSTGRES_HOST=localhost`) — passed (11)

**Breaking changes:** No

### [2026-03-28] — Complete TASK-005: Redis-ready caching rollout on high-cost read paths

**Task:** TASK-005 — Milestone 12 cross-service observability and security hardening
**Triggered by:** Continue after cross-service rate limiting rollout

**Changes:**
- `services/common/cache_service.py` — added shared JSON cache client with Redis-backed mode and in-memory fallback
- `services/product/app.py` — added GraphQL read-response caching with `X-Cache` hit/miss headers
- `services/user/accounts/views.py` — added user feed caching and invalidation on follow/unfollow/like/unlike/comment-create flows
- `services/product/test_product.py` — added response-cache regression test and cache reset in fixtures
- `services/user/accounts/tests.py` — added feed cache hit/invalidation regression tests and cache reset hooks

**Tests:**
- `pytest -q` in `services/product` (with `POSTGRES_HOST=localhost`) — passed (11)
- `python manage.py test accounts -v 2` in `services/user` (with `POSTGRES_HOST=localhost`) — passed (18)

**Breaking changes:** No

### [2026-03-28] — Continue TASK-005: cross-service rate limiting rollout

**Task:** TASK-005 — Milestone 12 cross-service observability and security hardening
**Triggered by:** Continue after logging parity completion

**Changes:**
- `services/common/rate_limit.py` — added shared rate limiter with Redis-backed mode and in-memory fallback
- `services/product/app.py` — added configurable GraphQL request rate limiting with HTTP 429 and `Retry-After`
- `services/order/app.py` — added configurable rate limiting for order create/status/process endpoints
- `services/chat/app.py` — added message-action rate limiting for websocket room traffic
- `services/user/userservice/rate_limit_middleware.py` — added middleware for auth/sensitive endpoint rate limiting
- `services/user/userservice/settings.py` — registered user rate-limit middleware
- `services/product/test_product.py` — added GraphQL rate-limit regression test and limiter reset fixture
- `services/order/test_order.py` — added order create rate-limit regression test and limiter reset fixture
- `services/chat/test_chat.py` — added limiter behavior unit test and import-path setup for shared module
- `services/user/accounts/tests.py` — added middleware-level auth/sensitive rate-limit tests

**Tests:**
- `pytest -q` in `services/product` (with `POSTGRES_HOST=localhost`) — passed (10)
- `pytest -q` in `services/order` (with `POSTGRES_HOST=localhost`) — passed (9)
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (5), skipped (2)
- `python manage.py test accounts -v 2` in `services/user` (with `POSTGRES_HOST=localhost`) — passed (16)

**Breaking changes:** No

### [2026-03-28] — Continue TASK-005: complete user-service structured logging parity

**Task:** TASK-005 — Milestone 12 cross-service observability and security hardening
**Triggered by:** Continue after shared logging rollout in product/chat/order

**Changes:**
- `services/user/userservice/middleware.py` — added structured request/exception logging middleware using shared logging service
- `services/user/userservice/settings.py` — registered middleware and enabled shared services module path

**Tests:**
- `python manage.py test accounts -v 2` in `services/user` (with `POSTGRES_HOST=localhost`) — passed (14 tests)

**Breaking changes:** No

### [2026-03-28] — Start TASK-005: shared structured logging rollout (product/chat/order)

**Task:** TASK-005 — Milestone 12 cross-service observability and security hardening
**Triggered by:** User request for robust logging service suitable for large-scale systems

**Changes:**
- `services/common/logging_service.py` — added queue-based structured JSON logging module with contextual binding helpers
- `services/product/app.py` — added request lifecycle logging, auth failure logging, and exception logging
- `services/order/app.py` — added request lifecycle logging, auth failure logging, and exception logging
- `services/chat/app.py` — added structured event logging for connection/auth/validation/broadcast flow

**Tests:**
- `pytest -q` in `services/product` — passed (9)
- `pytest -q` in `services/chat` — passed (4), skipped (2)
- `pytest -q` in `services/order` — passed (8)

**Breaking changes:** No

### [2026-03-28] — Close TASK-004 Milestone 11 cross-service productionization

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Final acceptance reconciliation and cross-service validation pass

**Changes:**
- `services/chat/chat_server.py` — converted legacy echo server into wrapper entrypoint delegating to `app.py`
- `.agent/TASKS.md` — marked TASK-004 complete and opened TASK-005 for milestone 12 work
- `.agent/CONTEXT.md` — switched focus from milestone 11 to milestone 12

**Tests:**
- `pytest -q` in `services/product` — passed (9)
- `pytest -q` in `services/chat` — passed (4), skipped (2)
- `pytest -q` in `services/order` — passed (8)

**Breaking changes:** No

### [2026-03-28] — Continue TASK-004: externalize order worker Celery config

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Follow-up hardening of order worker configuration debt

**Changes:**
- `services/order/celery_worker.py` — replaced hardcoded Redis broker/backend URLs with env-driven config (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`)
- `services/order/test_order.py` — added module reload test to verify Celery env override behavior

**Tests:**
- `pytest -q` in `services/order` (with `POSTGRES_HOST=localhost`) — passed (8 tests)

**Breaking changes:** No

### [2026-03-28] — Continue TASK-004: order service modular refactor and validation hardening

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Continue after chat service slice completion

**Changes:**
- `services/order/service.py` — added service-layer helpers for JWT policy, payload validation, and order CRUD/status operations
- `services/order/app.py` — moved route business logic to service layer and enforced strict validation + generic invalid-token handling
- `services/order/test_order.py` — replaced stale in-memory tests with DB-backed API tests for auth, create/get/status/process paths
- `services/order/models.py` — migrated to timezone-aware UTC timestamp default
- `services/order/celery_worker.py` — removed stdout print from worker task

**Tests:**
- `pytest -q` in `services/order` (with `POSTGRES_HOST=localhost`) — passed (7 tests)

**Breaking changes:**
- Order service now requires a strong `SERVICE_JWT_SECRET` at runtime and returns stricter payload validation errors.

### [2026-03-28] — Continue TASK-004: chat service modular refactor and validation hardening

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Continue after product security hardening

**Changes:**
- `services/chat/service.py` — added service-layer helpers for JWT secret policy, protocol-token extraction, payload validation, and DB message/history operations
- `services/chat/app.py` — refactored WebSocket handler to delegate to service helpers and return consistent validation errors
- `services/chat/test_chat.py` — added unit tests for validation helpers, improved integration test resiliency, and removed weak JWT test-key warning

**Tests:**
- `pytest -q` in `services/chat` (with `POSTGRES_HOST=localhost`) — passed (4 tests), skipped (2 integration tests when server not running)

**Breaking changes:**
- Chat startup now enforces strong `SERVICE_JWT_SECRET` via service helper checks.

### [2026-03-28] — Continue TASK-004: enforce product JWT runtime secret policy

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Continue execution to address security hardening item IMP-007

**Changes:**
- `services/product/app.py` — removed insecure JWT secret fallback, added minimum secret length enforcement, and fail-fast app startup check
- `services/product/app.py` — normalized invalid token response to avoid exposing decode internals
- `services/product/test_product.py` — added tests for invalid token response and weak-secret startup rejection

**Tests:**
- `pytest -q` in `services/product` (with `POSTGRES_HOST=localhost`) — passed (9 tests)

**Breaking changes:**
- Product service now raises startup error when `SERVICE_JWT_SECRET` is missing or too short.

### [2026-03-28] — Continue TASK-004: product validation hardening and warning cleanup

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** User request to proceed and fix warnings

**Changes:**
- `services/product/app.py` — added explicit request payload validation for GraphQL endpoint (`query` required)
- `services/product/schema.py` — added input validation for `searchProducts` arguments (`categoryId > 0`, bounded name length)
- `services/product/test_product.py` — set strong test JWT secret before app import, added missing-query and invalid-category validation tests

**Tests:**
- `pytest -q` in `services/product` (with `POSTGRES_HOST=localhost`) — passed (7 tests), warnings resolved

**Breaking changes:**
- Product `/graphql` now returns HTTP 400 for missing/invalid JSON payload query field.

### [2026-03-28] — Start TASK-004 with product service modular refactor slice

**Task:** TASK-004 — Milestone 11 cross-service productionization
**Triggered by:** Continue after user service M11 completion

**Changes:**
- `services/product/service.py` — introduced product service-layer query functions
- `services/product/schema.py` — migrated GraphQL resolvers to delegate data access to service layer
- `services/product/test_product.py` — added auth boundary and DB-backed GraphQL tests; stabilized fixture with unique seeded data and scoped session cleanup

**Tests:**
- `pytest -q` in `services/product` (with `POSTGRES_HOST=localhost`) — passed (5 tests)

**Breaking changes:** No

### [2026-03-28] — Complete M11-U4 query optimization in user service

**Task:** M11-U4 — Optimize queries to avoid N+1 issues
**Triggered by:** Continue execution after M11-U3 completion

**Changes:**
- `services/user/accounts/service.py` — added `select_related` optimization for feed, comments, followers, and following querysets
- `services/user/accounts/tests.py` — added query-count regression tests proving no N+1 on feed/follower paths

**Tests:**
- `python manage.py test accounts -v 2` (with `POSTGRES_HOST=localhost`) — passed (14 tests)

**Breaking changes:** No

### [2026-03-28] — Complete M11-U3 explicit validation hardening for user service

**Task:** M11-U3 — Add explicit input validation for all user endpoints
**Triggered by:** Continue execution after M11-U2 completion

**Changes:**
- `services/user/accounts/serializers.py` — added strict field validators (positive IDs, password minimum, profile update payload schema, comment constraints)
- `services/user/accounts/views.py` — introduced uniform structured validation error responses and endpoint-specific validation detail messages
- `services/user/accounts/tests.py` — expanded negative-path tests for invalid payload/query validation and profile/register validation

**Tests:**
- `python manage.py test accounts -v 2` (with `POSTGRES_HOST=localhost`) — passed (11 tests)

**Breaking changes:**
- Validation error response bodies now include an `errors` object for serializer-level failures.

### [2026-03-28] — Complete M11-U2 user service modular refactor

**Task:** M11-U2 — Refactor user service to enforce modular service-layer architecture
**Triggered by:** Continue execution after .agent initialization

**Changes:**
- `services/user/accounts/serializers.py` — added dedicated serializers and payload validators
- `services/user/accounts/views.py` — rewired views to thin orchestration and service calls
- `services/user/accounts/service.py` — added typed signatures and follower list query helpers
- `services/user/accounts/tests.py` — added validation and happy-path API tests for refactored endpoints

**Tests:**
- `python manage.py test accounts -v 2` (with `POSTGRES_HOST=localhost`) — passed (6 tests)

**Breaking changes:** No

### [2026-03-28] — Initialize .agent project knowledge base

**Task:** Bootstrap and populate required `.agent/` files
**Triggered by:** User request to initialize all files in `.agent/` from existing project structure docs

**Changes:**
- `.agent/REQUIREMENTS.md` — created with project scope, features, and non-functional requirements
- `.agent/STACK.md` — created with concrete stack and dependency versions
- `.agent/INSTRUCTIONS.md` — created with project coding and architecture conventions
- `.agent/SECURITY.md` — created with enforced auth and validation constraints
- `.agent/DECISIONS.md` — created with initial ADRs
- `.agent/CONTEXT.md` — created with current milestone and progress state
- `.agent/TASKS.md` — created with active objective and backlog
- `.agent/CHANGELOG.md` — created with bootstrap entry
- `.agent/IMPROVEMENTS.md` — created with initial debt observations

**Tests:** N/A (documentation/state initialization only)
**Breaking changes:** No
