# DECISIONS.md — Architecture Decision Records

## ADR-001: Use .agent knowledge base for persistent project memory
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
The project needs consistent context across sessions for roadmap state, security constraints, and architecture conventions.

**Options considered:**
1. Keep knowledge only in root docs and service READMEs.
2. Maintain dedicated `.agent/` operational files with specific purposes.

**Decision:**
Adopt option 2. Use `.agent/` files as the authoritative agent operating context, initialized from root project documents.

**Consequences:**
- Good: Faster, safer, and more consistent execution across sessions.
- Bad: Requires disciplined updates after each session.

---

## ADR-002: Enforce shared JWT for inter-service trust boundary
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** Project architecture (captured by ProjectAgent)

**Context:**
ShopSocial services call each other over HTTP/WebSocket. A uniform trust model is needed.

**Options considered:**
1. No inter-service auth (insecure).
2. Per-service custom auth schemes (complex and inconsistent).
3. Shared JWT with common secret and algorithm across services.

**Decision:**
Use shared JWT auth for all inter-service protected calls with `SERVICE_JWT_SECRET` and HS256.

**Consequences:**
- Good: Consistent verification and simpler cross-service integration.
- Bad: Secret rotation must be coordinated across all services.
- Risk: Secret compromise affects all service trust boundaries until rotation.

---

## ADR-003: Separate transport serializers from business orchestration in user service
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
The user service `views.py` mixed serializer declarations, payload validation, and queryset construction with endpoint orchestration, reducing modularity and making service-layer boundaries less explicit.

**Options considered:**
1. Keep serializers and views together in one module.
2. Extract serializers/payload validators into a dedicated module and keep views focused on request/response orchestration.

**Decision:**
Adopt option 2. Introduce `accounts/serializers.py`, keep business logic in `accounts/service.py`, and make views delegate to service functions.

**Consequences:**
- Good: Clearer separation of concerns and easier testability.
- Good: Better path for future validation hardening in M11-U3.
- Bad: Adds one more module to maintain.

---

## ADR-004: Standardize validation failure response envelope for user service
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
User endpoints previously returned inconsistent validation errors (single detail strings without field-level context), making clients and tests harder to reason about.

**Options considered:**
1. Keep endpoint-specific plain detail strings only.
2. Return a consistent envelope with a human detail plus serializer field errors.

**Decision:**
Adopt option 2 for serializer-driven validation failures: `{ "detail": <message>, "errors": <serializer_errors> }`.

**Consequences:**
- Good: Better client debuggability and explicit field-level validation feedback.
- Good: Easier automated testing of invalid payload scenarios.
- Bad: Error body shape differs from older simple detail-only responses for these paths.

---

## ADR-005: Use eager loading on user read paths to prevent N+1 regressions
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Feed/follower/comment reads can trigger N+1 related-object loads when serializers or business logic access user/post relationships across collections.

**Options considered:**
1. Keep default lazy loading and rely on future optimization passes.
2. Add explicit eager loading at service-layer queryset boundaries and protect with query-count tests.

**Decision:**
Adopt option 2 by adding `select_related` in `get_feed`, `get_followers`, `get_following`, and `get_comments`, plus query regression tests.

**Consequences:**
- Good: Stable query count and lower DB load under list endpoints.
- Good: Optimization intent becomes explicit in service layer.
- Bad: Requires maintenance when serializer access patterns evolve.

---

## ADR-006: Delegate product GraphQL resolver data access to service layer
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Product GraphQL resolvers contained direct query construction and filtering logic inside transport schema code, making modular evolution and testability harder.

**Options considered:**
1. Keep resolver-side query logic in `schema.py`.
2. Move data access/query behavior to a dedicated service module and keep resolvers as orchestration.

**Decision:**
Adopt option 2 by introducing `services/product/service.py` and delegating resolver access patterns to service functions.

**Consequences:**
- Good: Cleaner separation between transport and business/data access logic.
- Good: Easier path for future validation and performance optimization tasks.
- Bad: Adds another module that must remain aligned with schema contract.

---

## ADR-007: Enforce explicit GraphQL request and argument validation in product service
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Product GraphQL endpoint previously accepted loosely structured payloads and unvalidated resolver arguments, leading to inconsistent error handling.

**Options considered:**
1. Keep implicit GraphQL parser/engine error handling only.
2. Add explicit request-level and resolver-argument validation with clear error messages.

**Decision:**
Adopt option 2. Require non-empty `query` at HTTP boundary and validate `searchProducts` arguments (`categoryId` positive, name length bound) before service-layer execution.

**Consequences:**
- Good: More predictable input handling and safer API behavior.
- Good: Clearer failure semantics for clients and tests.
- Bad: Minor behavior change for malformed requests (returns 400 earlier).

---

## ADR-008: Enforce strong JWT secret requirement at product service startup
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Product service previously defaulted `SERVICE_JWT_SECRET` to a weak fallback value, which weakens inter-service token trust.

**Options considered:**
1. Keep weak fallback for convenience in local development.
2. Fail fast when secret is missing/weak and require explicit secure secret configuration.

**Decision:**
Adopt option 2. Enforce minimum secret length and startup failure if the secret is not configured securely.

**Consequences:**
- Good: Prevents accidental insecure runtime deployments.
- Good: Aligns with shared inter-service auth security requirements.
- Bad: Requires explicit env configuration in all runtime environments.

---

## ADR-009: Move chat WebSocket validation and persistence operations into service layer
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Chat WebSocket handler in `app.py` combined protocol parsing, JWT checks, payload validation, history reads, and message persistence in one large function.

**Options considered:**
1. Keep monolithic handler logic in `app.py`.
2. Extract reusable validation/persistence logic into service-layer helpers and keep handler orchestration-focused.

**Decision:**
Adopt option 2 by introducing `services/chat/service.py` and delegating token parsing, payload validation, and DB operations to that module.

**Consequences:**
- Good: Cleaner separation of concerns and easier unit testing for chat rules.
- Good: Better maintainability for future presence/rate-limit features.
- Bad: Slightly more indirection while debugging runtime flow.

---

## ADR-010: Consolidate order endpoint orchestration around service-layer validators and data operations
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Order Flask handlers previously mixed JWT checks, payload parsing, DB access, and webhook orchestration in route functions, and test coverage was tied to obsolete in-memory assumptions.

**Options considered:**
1. Keep route-centric logic and patch tests only.
2. Introduce explicit service-layer helpers for auth policy, payload validation, and persistence operations, with DB-backed tests.

**Decision:**
Adopt option 2 by adding `services/order/service.py`, delegating route business logic, and modernizing tests around persistent DB behavior.

**Consequences:**
- Good: Cleaner separation of concerns and more maintainable endpoint logic.
- Good: Validation and auth behavior become easier to test and reuse.
- Bad: Additional module introduces dependency mapping overhead.

---

## ADR-011: Configure order worker Celery endpoints through environment variables
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Order worker had hardcoded Redis broker/backend URLs, limiting deployment flexibility and conflicting with environment-based infrastructure configuration practices.

**Options considered:**
1. Keep hardcoded URLs and rely on network defaults.
2. Read broker/backend from env vars with sensible defaults aligned to compose.

**Decision:**
Adopt option 2 using `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` with default fallback to project Redis endpoint.

**Consequences:**
- Good: Better portability across environments.
- Good: Cleaner configuration management.
- Bad: Requires env management discipline to avoid misconfiguration.

---

## ADR-012: Consolidate chat startup path by delegating legacy entrypoint to primary app
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Chat service had two runnable entrypoints with divergent behavior (`app.py` production logic and `chat_server.py` legacy echo server), creating startup ambiguity.

**Options considered:**
1. Keep both files independent.
2. Remove `chat_server.py` entirely.
3. Keep compatibility file but delegate it to the canonical `app.py` main.

**Decision:**
Adopt option 3 to preserve compatibility while ensuring consistent runtime behavior.

**Consequences:**
- Good: Eliminates accidental startup of stale echo behavior.
- Good: Maintains backward compatibility for scripts still referencing `chat_server.py`.
- Bad: Small maintenance overhead for wrapper file.

---

## ADR-013: Adopt shared queue-based structured logging service for Python runtimes
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Milestone 12 requires observability improvements, and service-local ad-hoc logging patterns do not scale well for high-volume multi-service systems.

**Options considered:**
1. Keep per-service plain logging statements.
2. Add a shared structured logging utility with asynchronous queue handling and context propagation.

**Decision:**
Adopt option 2 by introducing `services/common/logging_service.py` and integrating it in product/chat/order runtimes.

**Consequences:**
- Good: Consistent, machine-parsable logs across services.
- Good: Queue-based dispatch reduces request-path logging overhead in high-throughput scenarios.
- Bad: Requires consistent adoption in remaining services (user service pending).

---

## ADR-014: Integrate shared logging in user service through Django middleware
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
User service required observability parity with Flask/WebSocket services while preserving Django request pipeline behavior.

**Options considered:**
1. Add ad-hoc logging in each view.
2. Add centralized middleware for request lifecycle and exception logging.

**Decision:**
Adopt option 2 with `userservice.middleware.RequestLoggingMiddleware` backed by shared logging service.

**Consequences:**
- Good: Consistent request/exception logging without per-view duplication.
- Good: Easier extension for correlation IDs and future metrics.
- Bad: Middleware order must be maintained to preserve intended behavior.

---

## ADR-015: Adopt shared configurable rate limiting with Redis-aware backend across services
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Milestone 12 requires rate limiting on sensitive/auth/order/chat/GraphQL paths. Implementing separate limiter logic per service risks drift and inconsistent behavior.

**Options considered:**
1. Implement service-local rate limiting independently in each runtime.
2. Use framework-native throttling only (mixed Django/Flask/WebSocket behavior).
3. Introduce a shared limiter utility with optional Redis backing and integrate per-service adapters.

**Decision:**
Adopt option 3 via `services/common/rate_limit.py`, using Redis when configured (`RATE_LIMIT_USE_REDIS=1` with `REDIS_URL`) and safe in-memory fallback otherwise.

**Consequences:**
- Good: Consistent throttle semantics and response patterns across services.
- Good: Better scale path through Redis-backed counters while keeping local-dev fallback.
- Good: Testability improved via shared reset hook used in service tests.
- Bad: In-memory fallback is process-local and less accurate under multi-instance deployments unless Redis is enabled.

---

## ADR-016: Use shared Redis-ready response caching for high-cost read paths
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Milestone 12 requires Redis caching for expensive reads, but introducing service-specific cache clients and key semantics in each service would duplicate logic and increase drift.

**Options considered:**
1. Implement independent caching logic in each service.
2. Use framework/plugin-specific caching per service stack.
3. Add a shared cache utility in `services/common` and integrate per-service cache key/adaptor logic.

**Decision:**
Adopt option 3 by introducing `services/common/cache_service.py` and applying it to product GraphQL read responses and user feed responses, with deterministic keying and short-TTL cache invalidation strategy.

**Consequences:**
- Good: Consistent Redis-ready cache behavior across services with graceful local fallback.
- Good: Faster implementation and easier testability via shared reset hooks.
- Good: Clear observability of cache effectiveness using response headers (`X-Cache`).
- Bad: Current invalidation is targeted to known write paths and may require expansion as new feed-affecting flows are added.

---

## ADR-017: Cache order read endpoint responses with write-path invalidation
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Order reads (`GET /orders/<id>`) are frequent and deterministic for a short interval. The endpoint can benefit from lightweight response caching while preserving consistency after order mutations.

**Options considered:**
1. Keep DB-only reads with no cache.
2. Cache reads with TTL only and no explicit invalidation.
3. Cache reads with short TTL plus explicit invalidation on create/status-update writes.

**Decision:**
Adopt option 3: cache `GET /orders/<id>` responses using shared cache utility and invalidate cache key on order create and status updates.

**Consequences:**
- Good: Reduced repeated DB reads for frequently polled order status.
- Good: Better freshness guarantees than TTL-only strategy.
- Bad: Additional write-path invalidation logic must be maintained when new order mutation endpoints are introduced.

---

## ADR-018: Cache chat room history reads with write-through invalidation on message persist
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Chat clients request recent room history on join and via explicit history actions. These reads are frequent and can be cached briefly, but must stay fresh after new message writes.

**Options considered:**
1. Keep DB-only history reads.
2. Cache history with TTL only.
3. Cache history with TTL and explicit invalidation when persisting new messages.

**Decision:**
Adopt option 3 using shared cache utility in chat service helpers with room+limit cache keys and invalidation on successful `save_chat_message`.

**Consequences:**
- Good: Reduces repeated room-history DB queries under reconnect/history-heavy usage.
- Good: Maintains fresher history immediately after writes.
- Bad: Invalidation currently targets configured history limit key; additional limits would need corresponding invalidation logic.

---

## ADR-019: Support prefix-based invalidation in shared cache utility for variable key spaces
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Chat history keys are parameterized by room and limit. Invalidation tied to one fixed key can leave stale cache entries for alternate limits.

**Options considered:**
1. Keep exact-key invalidation per default limit.
2. Track and invalidate a bounded set of known limit keys.
3. Add shared prefix-based invalidation support and invalidate by room key prefix.

**Decision:**
Adopt option 3 by extending `services/common/cache_service.py` with `delete_prefix`, and use room-level prefixes for chat history invalidation.

**Consequences:**
- Good: Correct invalidation even when multiple history limits are used.
- Good: Reusable grouped-invalidation primitive for future list/query cache keys.
- Bad: Redis prefix invalidation uses key scanning and should be used with bounded prefixes to avoid broad expensive scans.

---

## ADR-020: Emit structured debug metrics for cache prefix invalidation operations
**Date:** 2026-03-28
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Prefix invalidation is scan-based in Redis, and operational visibility is needed to detect unexpectedly expensive invalidation patterns.

**Options considered:**
1. Keep no telemetry for invalidation operations.
2. Emit unstructured print/debug logs.
3. Emit structured debug metrics with key counts and duration.

**Decision:**
Adopt option 3 by adding structured debug logging in `CacheClient.delete_prefix` with deleted key counts (Redis + memory) and `duration_ms`.

**Consequences:**
- Good: Easier diagnosis of high-cardinality invalidation behavior.
- Good: Reuses existing structured logging conventions and keeps metrics low-noise at debug level.
- Bad: Requires debug logging to be enabled in runtime environments where deep cache diagnostics are needed.

---

## ADR-021: Make cache prefix invalidation debug telemetry configurable and sampleable
**Date:** 2026-03-29
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
After introducing prefix invalidation telemetry, always-emitted debug events can become noisy in high-churn environments when debug logging is enabled globally.

**Options considered:**
1. Keep always-on debug emission for all invalidations.
2. Add only an on/off toggle.
3. Add both enable/disable toggle and probabilistic sampling.

**Decision:**
Adopt option 3 by adding `CACHE_PREFIX_INVALIDATION_DEBUG_ENABLED` and `CACHE_PREFIX_INVALIDATION_DEBUG_SAMPLE_RATE` controls, with defaults preserving existing full-fidelity behavior.

**Consequences:**
- Good: Operators can reduce log volume without removing observability entirely.
- Good: Targeted troubleshooting can still use full-fidelity mode.
- Bad: Sampling may omit individual events, so short windows can under-represent true invalidation frequency.

---

## ADR-022: Split order API and worker compose roles with health-gated dependencies
**Date:** 2026-03-29
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Compose previously ran the order service container with a worker command while exposing API port 7000, creating role ambiguity and integration startup failures.

**Options considered:**
1. Keep a single order container and manually switch command by environment.
2. Keep current setup and rely on external operator sequencing.
3. Define dedicated compose services for API and worker roles with explicit commands and health-gated dependency startup.

**Decision:**
Adopt option 3: use `order` for API (`python app.py`) and `order_worker` for Celery (`celery -A celery_worker.celery_app worker --loglevel=info`), and gate service startup on healthy db/redis dependencies.

**Consequences:**
- Good: Clear runtime role separation and correct API availability on port 7000.
- Good: More reliable startup behavior under cold boots via health-gated dependencies.
- Bad: Slightly higher compose complexity with one additional service.

---

## ADR-023: Build service images from shared services context for common module availability
**Date:** 2026-03-29
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Service images were built from per-service contexts, which excluded `services/common` and caused runtime import failures in containers (`ModuleNotFoundError: common`).

**Options considered:**
1. Duplicate `common` code into each service directory.
2. Keep per-service contexts and bind-mount `common` at runtime.
3. Build images from shared `services/` context and copy both service code and `common` module in Dockerfiles.

**Decision:**
Adopt option 3 to keep images self-contained and consistent across local runs and CI.

**Consequences:**
- Good: Eliminates runtime import failures for shared modules in containers.
- Good: Keeps compose smoke/integration checks reproducible without runtime bind-mount dependencies.
- Bad: Dockerfiles require path-specific COPY updates tied to shared build context layout.

---

## ADR-024: Use explicit product `/healthz` endpoint for readiness checks
**Date:** 2026-03-29
**Status:** accepted
**Decided by:** ProjectAgent

**Context:**
Product readiness previously relied on probing `/graphql` with an HTTP method that can yield non-health-related errors (for example, 500), creating noisy readiness signals.

**Options considered:**
1. Keep probing `/graphql` and accept non-deterministic status semantics.
2. Keep port-only socket checks.
3. Add explicit lightweight health endpoint and probe it from compose/smoke.

**Decision:**
Adopt option 3: add unauthenticated `/healthz` endpoint returning deterministic 200 payload and switch readiness probes to this route.

**Consequences:**
- Good: Clearer startup diagnostics and fewer false readiness negatives.
- Good: Decouples health verification from GraphQL transport/validation behavior.
- Bad: Introduces one additional public route that must remain stable.
