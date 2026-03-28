# TASKS.md — Task Tracker

## Active Objective
- Post-M12 read-path performance hardening

## In Progress

### TASK-011: Docker compose integration hardening
**Status:** completed
**Priority:** P2
**Effort:** M
**Type:** platform
**Assigned:** ProjectAgent
**Created:** 2026-03-29

**Description:**
Improve container orchestration correctness and startup reliability by aligning runtime commands with service roles and adding health-aware dependency sequencing.

**Acceptance Criteria:**
- [x] Order API and Celery worker run as separate compose services
- [x] Core services wait on healthy infrastructure dependencies
- [x] Compose configuration validates successfully

**Progress Notes:**
- Split order runtime into dedicated API and worker compose services.
- Added health checks for db/redis and core app services.
- Added health-gated dependency conditions and internal host overrides for db/redis.
- Validated compose configuration rendering with `docker compose config`.

### TASK-005: Milestone 12 cross-service observability and security hardening
**Status:** completed
**Priority:** P2
**Effort:** L
**Type:** platform
**Assigned:** ProjectAgent
**Created:** 2026-03-28

**Description:**
Implement structured logging, rate limiting, and cache-read optimization priorities across services.

**Progress Notes:**
- Introduced shared queue-based JSON logging service in `services/common/logging_service.py`.
- Integrated request lifecycle structured logging in product and order Flask services.
- Integrated structured event logging in chat WebSocket runtime with connection/room context.
- Verified no regressions via product/chat/order test suites.
- Integrated structured request/exception logging middleware in user Django service and validated existing user tests.
- Added shared rate-limiter utility (`services/common/rate_limit.py`) with Redis-backed mode and in-memory fallback.
- Added endpoint rate limiting for product GraphQL and order write/process routes.
- Added message rate limiting in chat runtime for `message` actions.
- Added Django middleware-based rate limiting for auth and sensitive user account endpoints.
- Validated new rate-limit regression coverage in product/order/chat/user test suites.
- Added shared cache utility (`services/common/cache_service.py`) with Redis-backed mode and in-memory fallback.
- Added response caching for high-cost product GraphQL read queries.
- Added user feed response caching with cache invalidation on follow/unfollow/like/unlike/comment-create flows.
- Added cache behavior regression tests for product and user services.

**Acceptance Criteria:**
- [x] Structured logging and exception observability added in user/product/chat/order services
- [x] Rate limiting added to sensitive/auth/order/chat/GraphQL endpoints
- [x] Redis caching integrated for high-cost read paths

---

## Backlog

### TASK-004: Milestone 11 cross-service productionization
**Status:** completed
**Priority:** P2
**Effort:** L
**Type:** platform
**Assigned:** ProjectAgent
**Created:** 2026-03-28

**Description:**
Complete pending Milestone 11 tasks for product, chat, and order services.

**Progress Notes:**
- Product service modular service-layer refactor started and merged (`schema.py` resolvers now delegate to `service.py`).
- Product service integration tests expanded and passing against Postgres-backed data.
- Product GraphQL input validation hardened for payload/query presence and search argument constraints.
- Product warnings cleaned in tests by enforcing strong JWT secret in test environment.
- Product runtime now enforces strong `SERVICE_JWT_SECRET` policy (no insecure fallback).
- Chat service refactored to use service-layer helpers for JWT parsing/validation, payload validation, and history/message persistence.
- Chat tests expanded with unit validation coverage and made resilient when WebSocket server is not running.
- Order service refactored with dedicated service-layer helpers for auth policy, payload validation, and data operations.
- Order API tests migrated from stale in-memory assumptions to DB-backed endpoint validation (7 passing).
- Order worker now reads Celery broker/backend from environment with test coverage for override behavior.
- Remaining: finalize cross-service acceptance criteria tracking and any remaining product/chat/order optimization tasks.

**Acceptance Criteria:**
- [x] Persistent DB integrated for product/chat/order service needs
- [x] Modular service-layer refactor completed for each remaining service
- [x] Input validation and scalability optimizations tracked and implemented

### TASK-002: M11-U3 explicit validation coverage
**Status:** completed
**Priority:** P1
**Effort:** M
**Type:** feature-hardening
**Assigned:** ProjectAgent
**Created:** 2026-03-28

**Description:**
Add explicit input validation for all user service endpoints beyond default serializer behavior where needed.

**Acceptance Criteria:**
- [x] Endpoint-level validation rules documented and enforced
- [x] Validation failures return structured errors
- [x] Tests added for invalid payload scenarios

### TASK-003: M11-U4 query optimization
**Status:** completed
**Priority:** P1
**Effort:** M
**Type:** performance
**Assigned:** ProjectAgent
**Created:** 2026-03-28

**Description:**
Optimize user feed/follower query patterns to avoid N+1 issues.

**Acceptance Criteria:**
- [x] Query count reduced for feed endpoint
- [x] Query count reduced for follower/following retrieval
- [x] Regression tests confirm unchanged response shape

### TASK-012: Compose smoke integration workflow
**Status:** completed
**Priority:** P2
**Effort:** M
**Type:** platform
**Assigned:** ProjectAgent
**Created:** 2026-03-29

**Description:**
Add a repeatable integration smoke workflow that boots docker compose services and verifies core API/WebSocket health and basic request flow.

**Acceptance Criteria:**
- [x] One-command smoke run for compose startup and health readiness
- [x] Basic auth-protected API checks for user/product/order
- [x] Basic chat connect/join flow validation

**Progress Notes:**
- Added executable smoke workflow script at `scripts/compose_smoke.sh` with startup, readiness, protected-route, and chat join checks.
- Added failure diagnostics (compose status + logs) to avoid silent readiness waits.
- Updated compose/build wiring so shared `common` package is available in all service images.
- Ensured runtime services receive strong `SERVICE_JWT_SECRET` from shell environment during smoke runs.
- Added WebSocket auth fallback support in chat for `Authorization: Bearer <token>` and fixed websockets 16 handler/header compatibility.

### TASK-013: Product deterministic readiness endpoint
**Status:** completed
**Priority:** P2
**Effort:** S
**Type:** platform
**Assigned:** ProjectAgent
**Created:** 2026-03-29

**Description:**
Eliminate ambiguous product readiness signals by exposing a dedicated health endpoint and wiring compose/smoke probes to that route.

**Acceptance Criteria:**
- [x] Product service exposes explicit unauthenticated health endpoint
- [x] Compose product healthcheck uses endpoint probe instead of port-open only
- [x] Smoke readiness waits on deterministic product 200 response

**Progress Notes:**
- Added `/healthz` route in product Flask app returning stable `{"service":"product","status":"ok"}` payload.
- Updated product compose healthcheck to HTTP probe `/healthz`.
- Updated smoke readiness check from `/graphql` to `/healthz`.
- Added product unit test for health endpoint response shape.

### TASK-014: Live docker runtime verification
**Status:** completed
**Priority:** P2
**Effort:** S
**Type:** verification
**Assigned:** ProjectAgent
**Created:** 2026-03-29

**Description:**
Verify the backend stack can be spun up in docker and passes end-to-end integration checks while remaining live.

**Acceptance Criteria:**
- [x] Compose stack starts successfully from clean state
- [x] End-to-end smoke checks pass across user/product/order/chat
- [x] Services remain up for manual follow-up verification

**Progress Notes:**
- Ran `docker compose down --remove-orphans` then `SMOKE_KEEP_UP=1 ./scripts/compose_smoke.sh`.
- Smoke checks passed and reported successful protected API + chat join validation.
- Verified live container health via `docker compose ps`.

## Done
| Task | Title | Completed | Notes |
|------|-------|-----------|-------|
| M11-U1 | Integrate persistent database for user service | already complete | Marked done in AGENT_CONTEXT and roadmap |
| TASK-000 | Initialize .agent knowledge base files | 2026-03-28 | Seeded from root project docs |
| TASK-001 | M11-U2 user service modular refactor | 2026-03-28 | Extracted serializers module, moved queryset access into service layer helpers, and validated with Django tests |
| TASK-002 | M11-U3 explicit validation coverage | 2026-03-28 | Added strict payload/query serializers, structured validation errors, and expanded negative-path test coverage |
| TASK-003 | M11-U4 query optimization | 2026-03-28 | Added select_related optimizations for feed/follower/comment reads and query-count regression tests |
| TASK-004 | M11 cross-service productionization | 2026-03-28 | Product/chat/order modular refactors, validation hardening, JWT policy checks, and DB-backed tests completed |
| TASK-005 | M12 observability/security hardening | 2026-03-28 | Completed structured logging, rate limiting, and Redis-ready caching rollout with regression tests |
| TASK-006 | Order read caching expansion | 2026-03-28 | Added cache hit/miss behavior for order reads and invalidation on order writes with regression tests |
| TASK-007 | Chat history caching expansion | 2026-03-28 | Added chat history cache hits and message-write invalidation with unit coverage and warning cleanup |
| TASK-008 | Chat prefix cache invalidation | 2026-03-28 | Generalized chat history invalidation to room prefix with shared cache delete_prefix support and unit tests |
| TASK-009 | Cache prefix metrics instrumentation | 2026-03-28 | Added debug metrics for cache prefix invalidation counts/duration and unit coverage |
| TASK-010 | Cache debug sampling controls | 2026-03-29 | Added env-configurable debug toggle and sampling for prefix invalidation telemetry with deterministic tests |
| TASK-011 | Docker compose integration hardening | 2026-03-29 | Split order API/worker services, added health checks and health-based dependencies, and fixed internal host wiring |
| TASK-012 | Compose smoke integration workflow | 2026-03-29 | Added one-command compose smoke script with protected API and chat join checks; fixed shared-module image context and websocket compatibility blockers |
| TASK-013 | Product deterministic readiness endpoint | 2026-03-29 | Added `/healthz` endpoint and switched compose/smoke product readiness probes to deterministic HTTP 200 health checks |
| TASK-014 | Live docker runtime verification | 2026-03-29 | Verified clean compose startup, successful smoke pass, and healthy running containers kept up for manual backend validation |

---

## Task Number Counter
Last task number used: **014**
