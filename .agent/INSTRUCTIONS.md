# INSTRUCTIONS.md — Coding Rules & Conventions

## General Philosophy
- Clarity over cleverness.
- Keep services modular and enforce service-layer boundaries.
- Avoid cross-layer leakage from views/routes directly to storage when service functions exist.
- Keep changes minimal and localized.

## Architecture Conventions
- Follow service-layer design in each service:
  - Transport/API layer: request parsing, response shaping, auth boundary.
  - Service layer: business logic orchestration.
  - Data/model layer: persistence and ORM interaction.
- Prefer explicit DTO-like payload handling at service boundaries.
- Keep inter-service contracts stable and backwards compatible unless explicitly planned.

## Python Rules
- Use type hints on new or refactored functions.
- No unused imports or dead code.
- Avoid broad exception swallowing; catch specific exceptions when possible.
- Do not introduce debug print statements.

## API Rules
- Use structured JSON error responses with explicit status codes.
- Validate input at API boundaries; never trust client payloads.
- Protected endpoints must verify JWT before processing.

## Inter-service Auth Rules
- HTTP: `Authorization: Bearer <token>`
- WebSocket: `Sec-WebSocket-Protocol: jwt=<token>`
- Signing: HS256 with shared `SERVICE_JWT_SECRET`
- Validate token on every protected endpoint.

## Testing Rules
- Add or update tests alongside behavior changes.
- Prefer pytest tests for Flask/chat/order services and Django test framework for user service.
- No skipped tests merged without explicit reason.

## Session Hygiene
- Update .agent state files at session end:
  - CONTEXT.md
  - TASKS.md
  - CHANGELOG.md
  - IMPROVEMENTS.md
  - DECISIONS.md (if a new architectural choice was made)

## Pre-task Checklist
- [ ] Requirements and security constraints reviewed
- [ ] Affected service context reviewed
- [ ] Tests planned before or with implementation
- [ ] No secrets added to source files
