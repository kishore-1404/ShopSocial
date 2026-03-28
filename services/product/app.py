
from flask import Flask, request, jsonify, g

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import hashlib
import json
import os
import sys
import time
import uuid
import jwt
from functools import wraps
from pathlib import Path

SERVICES_DIR = Path(__file__).resolve().parent.parent
if str(SERVICES_DIR) not in sys.path:
    sys.path.append(str(SERVICES_DIR))

from common.logging_service import bind_context, clear_context, configure_logging, get_logger
from common.cache_service import get_cache_client
from common.rate_limit import get_rate_limiter

MIN_SECRET_LENGTH = 32

# Database config
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'shopsocial')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'shopsocial')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'shopsocial')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'db')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
configure_logging("product")
logger = get_logger(__name__, "product")
cache_client = get_cache_client()
rate_limiter = get_rate_limiter()


def _get_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _enforce_graphql_rate_limit() -> tuple[bool, int]:
    limit = _get_positive_int_env("PRODUCT_GRAPHQL_RATE_LIMIT", 120)
    window = _get_positive_int_env("PRODUCT_GRAPHQL_RATE_WINDOW_SECONDS", 60)
    client_key = request.headers.get("X-Forwarded-For") or request.remote_addr or "unknown"
    return rate_limiter.allow(f"product:graphql:{client_key}", limit, window)


def _is_cacheable_graphql_query(query: str) -> bool:
    normalized = query.strip().lower()
    return not normalized.startswith("mutation")


def _graphql_cache_ttl() -> int:
    return _get_positive_int_env("PRODUCT_GRAPHQL_CACHE_TTL", 30)


def _graphql_cache_key(query: str, variables, operation_name) -> str:
    payload = json.dumps(
        {
            "query": query,
            "variables": variables,
            "operation_name": operation_name,
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"product:graphql:response:{digest}"


def get_service_jwt_secret() -> str:
    secret = os.environ.get("SERVICE_JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"SERVICE_JWT_SECRET must be set and at least {MIN_SECRET_LENGTH} characters"
        )
    return secret

def create_tables():
    Base.metadata.create_all(bind=engine)

def require_service_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            logger.warning("auth_header_missing", extra={"event": "auth_failed"})
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            jwt.decode(token, get_service_jwt_secret(), algorithms=["HS256"])
        except Exception:
            logger.warning("invalid_jwt", extra={"event": "auth_failed"})
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def create_app() -> Flask:
    """Create and configure the Flask application."""
    get_service_jwt_secret()
    app = Flask(__name__)
    create_tables()

    @app.before_request
    def _before_request():
        g.request_start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        bind_context(request_id=request_id)

    @app.after_request
    def _after_request(response):
        duration_ms = round((time.perf_counter() - g.request_start) * 1000, 3)
        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        clear_context()
        return response

    @app.errorhandler(Exception)
    def _handle_unexpected_error(err):
        logger.exception("unexpected_error", extra={"event": "unexpected_error"})
        return jsonify({"error": "Internal server error"}), 500

    @app.route('/healthz', methods=['GET'])
    def healthz():
        return jsonify({"service": "product", "status": "ok"}), 200

    from schema import schema  # Import here to avoid circular import

    @app.route('/graphql', methods=['POST'])
    @require_service_jwt
    def graphql_server():
        allowed, retry_after = _enforce_graphql_rate_limit()
        if not allowed:
            logger.warning("rate_limit_exceeded", extra={"event": "rate_limited"})
            return (
                jsonify({"error": "Rate limit exceeded", "retry_after": retry_after}),
                429,
                {"Retry-After": str(retry_after)},
            )

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON payload"}), 400

        query = data.get('query')
        if not isinstance(query, str) or not query.strip():
            return jsonify({"error": "Field `query` is required"}), 400

        variables = data.get('variables')
        operation_name = data.get('operationName')

        cacheable = _is_cacheable_graphql_query(query)
        cache_key = _graphql_cache_key(query, variables, operation_name) if cacheable else None
        if cacheable and cache_key:
            cached_response = cache_client.get_json(cache_key)
            if isinstance(cached_response, dict):
                response = jsonify(cached_response)
                response.headers["X-Cache"] = "HIT"
                return response

        # Pass DB session in context
        db = SessionLocal()
        try:
            result = schema.execute(
                query,
                variables=variables,
                context_value={"request": request, "db": db},
                operation_name=operation_name
            )
            response = {}
            if result.errors:
                response['errors'] = [str(e) for e in result.errors]
            if result.data:
                response['data'] = result.data

            if cacheable and cache_key and not result.errors and "data" in response:
                cache_client.set_json(cache_key, response, _graphql_cache_ttl())

            flask_response = jsonify(response)
            flask_response.headers["X-Cache"] = "MISS" if cacheable else "BYPASS"
            return flask_response
        finally:
            db.close()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
