# SECURITY.md — Security Rules

> These rules are mandatory and override implementation convenience.

## 1. Secrets Management
- Never hardcode credentials, tokens, API keys, or private connection strings.
- Read secrets from environment variables only.
- Never log secrets or raw Authorization headers.

## 2. Inter-service Authentication (Required)
All internal API calls between services require JWT.

- HTTP header: `Authorization: Bearer <token>`
- WebSocket protocol header: `Sec-WebSocket-Protocol: jwt=<token>`
- Shared secret env var: `SERVICE_JWT_SECRET`
- Algorithm: HS256

Validation requirements:
- Validate token on every protected endpoint.
- Reject missing, malformed, expired, or invalid signature tokens.
- Rotate `SERVICE_JWT_SECRET` across all services to invalidate old tokens.

## 3. Authentication and Authorization
- Do not trust client-provided user IDs without server-side checks.
- Enforce resource-level permission checks where applicable.
- Keep auth required on all endpoints marked protected in service contexts.

## 4. Input Validation
- Validate and sanitize all incoming payloads.
- Do not pass unvalidated user input into SQL queries, shell commands, or dynamic evaluators.
- Apply explicit schema/serializer validation beyond implicit defaults where required by roadmap tasks.

## 5. Data Handling and Privacy
- Avoid logging personally identifiable information unless explicitly required and protected.
- Return minimum required fields in API responses.
- Passwords must be hashed using framework-supported secure mechanisms.

## 6. Operational Controls
- Rate limiting is required for auth and sensitive endpoints (tracked as pending tasks).
- Structured logging and observability are required for production readiness.
- Security-relevant failures should be logged as events without leaking sensitive payloads.

## 7. Security Stop Conditions
Halt and seek operator confirmation if asked to:
- Disable JWT auth on protected endpoints.
- Expose or print secrets.
- Bypass validation for convenience in production paths.
