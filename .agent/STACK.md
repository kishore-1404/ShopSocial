# STACK.md — Technology Stack

## Core Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language | Python | 3.x | Unified language across services |
| User service framework | Django | 6.0.3 | REST API with social features |
| API toolkit | Django REST Framework | 3.16.1 | User service APIs |
| Auth | djangorestframework-simplejwt | 5.5.1 | JWT for user auth |
| Product service framework | Flask + Graphene GraphQL | Flask 3.1.3 / Graphene 3.4.3 | Product catalog and posts |
| Chat transport | websockets | 16.0 | Real-time service |
| Order async | Celery | 5.6.2 | Background processing |
| Message/cache broker | Redis | 7.3.0 (client) | Caching and Celery broker |
| SQL ORM | SQLAlchemy | 2.0.48 | Flask services data models |
| Relational DB | PostgreSQL | via psycopg2-binary 2.9.11 | Persistent service storage |
| Containerization | Docker + docker-compose | current repo config | Local orchestration |
| Testing | pytest / pytest-asyncio | 9.0.2 / 1.3.0 | Service-level tests |

## Backend Dependencies (Pinned)
| Package | Version | Purpose |
|---------|---------|---------|
| django | 6.0.3 | User service framework |
| djangorestframework | 3.16.1 | API layer |
| djangorestframework-simplejwt | 5.5.1 | JWT auth |
| flask | 3.1.3 | Product/order API framework |
| graphene | 3.4.3 | GraphQL schema and execution |
| celery | 5.6.2 | Background jobs |
| redis | 7.3.0 | Redis integration |
| sqlalchemy | 2.0.48 | ORM for non-Django services |
| psycopg2-binary | 2.9.11 | PostgreSQL driver |
| websockets | 16.0 | Chat service transport |
| pyjwt | 2.12.1 | JWT operations in non-Django services |
| requests | 2.32.5 | Inter-service HTTP calls |

## External Services
| Service | Purpose | Notes |
|---------|---------|-------|
| PostgreSQL | Persistent relational storage | Shared infrastructure service |
| Redis | Cache and task broker | Used for Celery and future caching |
| Webhook targets | Order status callbacks | External integration endpoint |

## Environment Variables
```bash
SERVICE_JWT_SECRET=...        # Shared secret for inter-service JWT validation (HS256)
DATABASE_URL=...              # Service database connection string
REDIS_URL=...                 # Redis connection string
JWT_ACCESS_LIFETIME=...       # Optional token lifetime config
DJANGO_SECRET_KEY=...         # Django application secret
DEBUG=...                     # Service debug flag (non-production)
```

## Version History
| Date | Change |
|------|--------|
| 2026-03-28 | Initialized from service requirements and repository architecture |
