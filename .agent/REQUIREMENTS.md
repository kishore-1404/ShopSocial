# REQUIREMENTS.md — Project Requirements

## Project Overview
**Project Name:** ShopSocial
**Owner:** kishore-1404
**Started:** 2026
**Version:** 0.1.0

### One-line summary
ShopSocial is a microservices-based social commerce backend combining user social features, product discovery, real-time chat, and order processing.

### Problem it solves
It provides a single platform where users can discover products, socialize around product content, chat in real time, and place/process orders across coordinated services.

### Target users
- End users who browse products, follow creators/users, and interact socially.
- Internal service clients in a distributed backend that communicate through authenticated service-to-service APIs.

---

## Goals & Success Metrics
| Goal | Metric | Target |
|------|--------|--------|
| Reliable service integration | Internal API auth coverage | 100% protected inter-service endpoints validate JWT |
| Scalable backend architecture | Persistent storage adoption | All core services migrated from in-memory to persistent DB |
| Maintainable codebase | Architecture compliance | Service-layer modular architecture enforced per service |
| Secure input handling | Validation coverage | Explicit input validation on all endpoints |

---

## Core Features

### Feature 1: User Management and Social Graph
**Status:** implemented
**Priority:** High
**Acceptance Criteria:**
- [x] User registration/login with JWT
- [x] User profiles
- [x] Follow/unfollow and social feed
- [x] Like/unlike and comments

### Feature 2: Product and Post Service (GraphQL)
**Status:** implemented (in-memory persistence remains technical debt)
**Priority:** High
**Acceptance Criteria:**
- [x] Product catalog
- [x] Product posts
- [x] Flexible GraphQL queries
- [x] Product search

### Feature 3: Real-time Product Chat
**Status:** implemented (database persistence and presence still pending productionization)
**Priority:** High
**Acceptance Criteria:**
- [x] Chat rooms per product
- [x] Real-time messaging
- [x] Product sharing context by product room
- [ ] Online status tracking
- [ ] Database-backed history persistence

### Feature 4: Order Processing and Background Jobs
**Status:** implemented (persistent DB migration pending)
**Priority:** High
**Acceptance Criteria:**
- [x] Order creation and lifecycle updates
- [x] Webhook notifications
- [x] Celery background processing
- [ ] Persistent order storage

---

## Non-Functional Requirements
- Performance: efficient query patterns and background processing for expensive workflows.
- Security: JWT authentication, inter-service JWT validation, input validation, rate limiting.
- Scalability: Redis caching, Celery workers, persistent storage for all services.
- Observability: structured logging, explicit error handling, and consistent API error responses.
- Architecture: modular service-layer design with clear separation of concerns.

---

## Out of Scope
- Frontend UI implementation.
- Payment gateway integration beyond current order lifecycle scope.

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2026-03-28 | Initialized from PROJECT_REQUIREMENTS.md, DEVELOPMENT_ROADMAP.md, and AGENT_CONTEXT.md | ProjectAgent |
