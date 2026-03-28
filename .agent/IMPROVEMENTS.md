# IMPROVEMENTS.md — Improvement Backlog

## Priority Legend
- P0: Immediate security/blocking issue
- P1: High-impact debt slowing current milestone
- P2: Medium-term maintainability/scalability
- P3: Nice-to-have improvements

## Active Items

### IMP-021: Add lightweight runtime status command helper
**Priority:** P3
**Effort:** S
**Found:** 2026-03-29
**Location:** scripts/

**Observation:**
After successful smoke startup with services kept running, operators still manually run multiple compose commands to inspect status/logs.

**Why it matters:**
Repeated manual checks can slow verification workflows and create inconsistent triage steps.

**Suggested approach:**
Add a small helper script (for example, `scripts/compose_status.sh`) that prints `compose ps` plus concise tail logs for core services.

**Promoted to task?** Not yet

### IMP-019: Add explicit product health endpoint for compose/readiness probes
**Priority:** P2
**Effort:** S
**Found:** 2026-03-29
**Location:** services/product/app.py

**Observation:**
Current smoke readiness check against product GraphQL endpoint can return HTTP 500 for plain GET requests before structured GraphQL request validation paths.

**Why it matters:**
Readiness automation should probe a deterministic lightweight health route (HTTP 200) to avoid false negatives and confusing startup signals.

**Suggested approach:**
Expose a simple unauthenticated `/healthz` endpoint in product service and update compose/smoke readiness checks to target that route.

**Promoted to task?** Implemented

**Status update (2026-03-29):**
Implemented via product `/healthz` route and compose/smoke probe updates.

### IMP-020: Add no-build mode for compose smoke reruns
**Priority:** P3
**Effort:** S
**Found:** 2026-03-29
**Location:** scripts/compose_smoke.sh

**Observation:**
Smoke workflow currently forces `docker compose up -d --build` on each run, which slows repeated integration reruns during debugging.

**Why it matters:**
Long rebuild cycles reduce iteration speed for operational validation tasks.

**Suggested approach:**
Add optional flag/env toggle to skip image rebuild when code has not changed (for example, `SMOKE_NO_BUILD=1`).

**Promoted to task?** Not yet

### IMP-018: Enforce strong compose startup secret validation
**Priority:** P2
**Effort:** S
**Found:** 2026-03-29
**Location:** docker-compose.yml / runtime env management

**Observation:**
Current compose runtime still accepts weak values for `SERVICE_JWT_SECRET` from local `.env` files, which can cause insecure local defaults or service startup failures in strict validation paths.

**Why it matters:**
Inter-service auth integrity depends on strong shared secrets; weak defaults increase accidental insecure runs and inconsistent startup behavior.

**Suggested approach:**
Add an `.env.example` security baseline and compose-time required-variable checks/documentation for `SERVICE_JWT_SECRET` length expectations.

**Promoted to task?** Not yet

### IMP-014: Generalize chat history cache invalidation for variable history limits
**Priority:** P3
**Effort:** S
**Found:** 2026-03-28
**Location:** services/chat/service.py

**Observation:**
Current chat invalidation targets the default history limit cache key (`limit=50`), which is sufficient for current flows but may miss alternate history limits if introduced later.

**Why it matters:**
Future clients requesting different limits could receive stale history after writes unless invalidation is broadened.

**Suggested approach:**
Track invalidation by room prefix or maintain a small per-room index of active history keys to invalidate on write.

**Promoted to task?** Implemented

**Status update (2026-03-28):**
Implemented via shared `delete_prefix` cache utility and room-prefix invalidation in chat service.

### IMP-015: Add bounded metrics around prefix invalidation scan cost
**Priority:** P3
**Effort:** S
**Found:** 2026-03-28
**Location:** services/common/cache_service.py

**Observation:**
Redis prefix invalidation currently uses scan + delete without explicit instrumentation on keys deleted.

**Why it matters:**
Operational visibility into invalidation fan-out helps detect accidental high-cardinality cache key patterns.

**Suggested approach:**
Emit structured debug metrics/event counters for prefix invalidation key counts in non-hot-path admin/maintenance context.

**Promoted to task?** Implemented

**Status update (2026-03-28):**
Implemented via structured debug metrics in `CacheClient.delete_prefix` with deleted key counts and duration tracking.

### IMP-016: Add optional sampling guard for high-frequency debug invalidation logs
**Priority:** P3
**Effort:** S
**Found:** 2026-03-28
**Location:** services/common/cache_service.py

**Observation:**
Prefix invalidation debug events are now emitted for every operation, which may be noisy in very high-churn cache patterns when debug logging is globally enabled.

**Why it matters:**
Log-volume spikes can reduce signal-to-noise ratio in local diagnostics and stress log pipelines in verbose environments.

**Suggested approach:**
Add optional sampling/env toggle for cache invalidation debug events while preserving full fidelity in targeted troubleshooting sessions.

**Promoted to task?** Implemented

**Status update (2026-03-29):**
Implemented with `CACHE_PREFIX_INVALIDATION_DEBUG_ENABLED` and `CACHE_PREFIX_INVALIDATION_DEBUG_SAMPLE_RATE` controls in shared cache service plus deterministic regression tests.

### IMP-017: Add structured reason tags for cache invalidation debug events
**Priority:** P3
**Effort:** S
**Found:** 2026-03-29
**Location:** services/common/cache_service.py

**Observation:**
Current prefix invalidation telemetry captures counts and duration but not an explicit operation reason/source tag.

**Why it matters:**
When multiple call sites share a cache prefix pattern, identifying which flow generated high invalidation churn is slower.

**Suggested approach:**
Allow optional caller-provided reason tags (for example, `chat_message_persist`) in `delete_prefix` debug metadata.

**Promoted to task?** Not yet

### IMP-013: Add paginated cache strategy for future order list endpoints
**Priority:** P3
**Effort:** M
**Found:** 2026-03-28
**Location:** services/order/app.py

**Observation:**
Current caching covers single-order reads only; future list/query endpoints will need pagination-aware cache keying and scoped invalidation to avoid high cardinality or stale list pages.

**Why it matters:**
List caching done incorrectly can increase memory pressure and create hard-to-debug stale data windows.

**Suggested approach:**
Define canonical query key normalization (page, size, status filters) and pair with short TTL plus selective invalidation per status transition.

**Promoted to task?** Not yet

### IMP-012: Expand feed cache invalidation coverage to creator-side mutations
**Priority:** P2
**Effort:** M
**Found:** 2026-03-28
**Location:** services/user/accounts/views.py

**Observation:**
User feed cache currently invalidates on viewer actions (follow/unfollow/like/unlike/comment create), but future creator-side post mutations (new post/edit/delete endpoints) will also require fan-out invalidation semantics.

**Why it matters:**
Without broader invalidation strategy, followers may temporarily see stale feed content after creator updates.

**Suggested approach:**
Introduce explicit feed-cache invalidation helpers at post write boundaries and evaluate event-driven invalidation for follower sets when post-creation APIs are added.

**Promoted to task?** Not yet

### IMP-011: Expand rate-limit key strategy beyond client IP for NAT-heavy traffic
**Priority:** P2
**Effort:** M
**Found:** 2026-03-28
**Location:** services/common/rate_limit.py and per-service adapters

**Observation:**
Current route/message throttling primarily keys by client IP (and route/room context), which can unfairly throttle multiple users behind shared NAT/proxy egress.

**Why it matters:**
False-positive rate limiting can degrade user experience in enterprise/mobile carrier networks.

**Suggested approach:**
Blend stable user/service identity into keys for authenticated flows (e.g., JWT `sub`/service claim) while preserving IP fallback for anonymous/auth endpoints.

**Promoted to task?** Not yet

### IMP-010: Complete structured logging parity in user service
**Priority:** P1
**Effort:** M
**Found:** 2026-03-28
**Location:** services/user

**Observation:**
Shared structured logging is now integrated in product/chat/order, but user service still needs equivalent request/error instrumentation for consistent observability.

**Why it matters:**
Cross-service incident analysis is weaker when one core service emits inconsistent log shape.

**Suggested approach:**
Apply the shared logging service pattern to Django middleware/view error paths in user service.

**Promoted to task?** Implemented

**Status update (2026-03-28):**
Implemented via `userservice.middleware.RequestLoggingMiddleware` and settings integration.

### IMP-009: Externalize hardcoded Celery broker/backend URLs in order worker
**Priority:** P2
**Effort:** S
**Found:** 2026-03-28
**Location:** services/order/celery_worker.py

**Observation:**
Order worker currently hardcodes Redis URLs for broker/backend instead of reading environment-configured values.

**Why it matters:**
Hardcoded infrastructure endpoints reduce deployment flexibility and can break non-default environments.

**Suggested approach:**
Read broker/backend from env vars with safe defaults consistent with project compose config.

**Promoted to task?** Implemented

**Status update (2026-03-28):**
Implemented using `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` plus test coverage for env override behavior.

### IMP-008: Align chat entrypoints to avoid stale runtime ambiguity
**Priority:** P2
**Effort:** S
**Found:** 2026-03-28
**Location:** services/chat/app.py and services/chat/chat_server.py

**Observation:**
Chat service has two server files; `app.py` contains production chat logic while `chat_server.py` is a legacy echo server.

**Why it matters:**
This can cause accidental startup of the wrong server implementation and inconsistent behavior.

**Suggested approach:**
Either remove `chat_server.py` or convert it into a thin wrapper importing `app.py` main entrypoint.

**Promoted to task?** Implemented

**Status update (2026-03-28):**
Implemented by converting `chat_server.py` into a wrapper that delegates to `app.py` main.

### IMP-007: Remove insecure JWT fallback default from product service
**Priority:** P1
**Effort:** S
**Found:** 2026-03-28
**Location:** services/product/app.py

**Observation:**
Product service falls back to `SERVICE_JWT_SECRET="changeme"`, and tests surfaced weak-key warnings from jwt library.

**Why it matters:**
Weak/default secrets significantly reduce token integrity guarantees and can allow forged inter-service tokens.

**Suggested approach:**
Fail fast when `SERVICE_JWT_SECRET` is missing/weak in non-test mode, and enforce minimum secret length policy.

**Promoted to task?** Not yet

**Status update (2026-03-28):**
Implemented: product runtime now enforces minimum secret length and fails fast for weak/missing `SERVICE_JWT_SECRET`; tests added for policy enforcement.

### IMP-006: Add endpoint-level query budget assertions for API responses
**Priority:** P2
**Effort:** M
**Found:** 2026-03-28
**Location:** user API list endpoints (`feed`, `followers`, `following`, `comments`)

**Observation:**
Current regression tests validate service-layer query behavior, but endpoint-level query budgets are not explicitly enforced.

**Why it matters:**
Future view/serializer changes could reintroduce query inflation even if service helpers stay optimized.

**Suggested approach:**
Add API-level query count tests around authenticated GET endpoints with deterministic fixtures.

**Promoted to task?** Not yet

### IMP-005: Formalize API error contract in service README/docs
**Priority:** P2
**Effort:** S
**Found:** 2026-03-28
**Location:** services/user API behavior documentation

**Observation:**
Validation errors now return a structured envelope with both `detail` and `errors`, but this contract is not documented in the user service README/context files.

**Why it matters:**
Undocumented response contracts can break client assumptions during integration.

**Suggested approach:**
Document the standard error schema and examples for all validation-failure endpoints.

**Promoted to task?** Not yet

### IMP-004: Add dedicated local test settings to avoid host override friction
**Priority:** P2
**Effort:** S
**Found:** 2026-03-28
**Location:** services/user/userservice/settings.py

**Observation:**
Running Django tests from host shell requires manually overriding `POSTGRES_HOST=localhost` because default settings expect compose-network hostname `db`.

**Why it matters:**
This creates avoidable test friction and can hide regressions when contributors skip local test runs.

**Suggested approach:**
Introduce a separate test settings module or conditional host fallback for local test execution.

**Promoted to task?** Not yet

### IMP-001: Duplicate and drift-prone dependency declarations across service requirement files
**Priority:** P2
**Effort:** S
**Found:** 2026-03-28
**Location:** requirements files at repo root and each service

**Observation:**
Current requirements files appear to contain a large shared dependency set across all services, increasing update overhead and drift risk.

**Why it matters:**
Dependencies can diverge unintentionally, and unnecessary packages may inflate service images and attack surface.

**Suggested approach:**
Split into shared base requirements and service-specific requirement overlays, or regenerate per-service lock files from minimal manifests.

**Promoted to task?** Not yet

---

### IMP-002: Milestone status duplication between roadmap and agent context
**Priority:** P3
**Effort:** S
**Found:** 2026-03-28
**Location:** AGENT_CONTEXT.md and DEVELOPMENT_ROADMAP.md

**Observation:**
Progress state is tracked in multiple files, which can drift without a defined source of truth.

**Why it matters:**
Inconsistent milestone status can mislead implementation priorities.

**Suggested approach:**
Define one authoritative status file and generate summaries to other docs from it.

**Promoted to task?** Not yet

---

### IMP-003: Pending production hardening tasks across all services
**Priority:** P1
**Effort:** L
**Found:** 2026-03-28
**Location:** Milestone 11 and 12 roadmap items

**Observation:**
Multiple services still lack complete validation, modularization, caching, observability, and rate limiting.

**Why it matters:**
These gaps increase operational risk and reduce production readiness.

**Suggested approach:**
Create service-by-service hardening epics with measurable acceptance criteria and test gates.

**Promoted to task?** Partially (tracked in TASKS backlog)

---

## Closed / Archived
| ID | Title | Resolution Date | Notes |
|----|-------|------------------|-------|
| — | — | — | — |
