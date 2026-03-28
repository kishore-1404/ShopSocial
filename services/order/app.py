
from flask import Flask, jsonify, request, g

from models import Order, Base
from celery_worker import process_order
import requests
import os
import sys
import time
import uuid
from functools import wraps
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

SERVICES_DIR = Path(__file__).resolve().parent.parent
if str(SERVICES_DIR) not in sys.path:
    sys.path.append(str(SERVICES_DIR))

from common.logging_service import bind_context, clear_context, configure_logging, get_logger
from common.cache_service import get_cache_client
from common.rate_limit import get_rate_limiter
from service import (
    create_order as create_order_record,
    get_order_by_id,
    get_service_jwt_secret,
    update_order_status as update_order_status_record,
    validate_create_order_payload,
    validate_service_jwt,
    validate_status_payload,
)


app = Flask(__name__)
configure_logging("order")
logger = get_logger(__name__, "order")
cache_client = get_cache_client()
rate_limiter = get_rate_limiter()


def _get_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _enforce_rate_limit(scope: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    client_key = request.headers.get("X-Forwarded-For") or request.remote_addr or "unknown"
    return rate_limiter.allow(f"order:{scope}:{client_key}", limit, window_seconds)


def _rate_limited_response(retry_after: int):
    logger.warning("rate_limit_exceeded", extra={"event": "rate_limited"})
    return (
        jsonify({"error": "Rate limit exceeded", "retry_after": retry_after}),
        429,
        {"Retry-After": str(retry_after)},
    )


def _order_cache_ttl() -> int:
    return _get_positive_int_env("ORDER_READ_CACHE_TTL", 30)


def _order_cache_key(order_id: int) -> str:
    return f"order:read:{order_id}"


def _invalidate_order_cache(order_id: int) -> None:
    cache_client.delete(_order_cache_key(order_id))

# Database config
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'shopsocial')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'shopsocial')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'shopsocial')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'db')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

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
        if not validate_service_jwt(token, get_service_jwt_secret(os.environ)):
            logger.warning("invalid_jwt", extra={"event": "auth_failed"})
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


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




@app.route('/orders/<int:order_id>/process', methods=['POST'])
@require_service_jwt
def process_order_bg(order_id):
    limit = _get_positive_int_env("ORDER_PROCESS_RATE_LIMIT", 30)
    window = _get_positive_int_env("ORDER_PROCESS_RATE_WINDOW_SECONDS", 60)
    allowed, retry_after = _enforce_rate_limit("process", limit, window)
    if not allowed:
        return _rate_limited_response(retry_after)

    db = SessionLocal()
    try:
        order = get_order_by_id(db, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        task = process_order.delay(order_id)
        return jsonify({"task_id": task.id, "status": "processing"})
    finally:
        db.close()



@app.route('/')
def index():
    return jsonify({"service": "order", "status": "ok"})


@app.route('/orders', methods=['POST'])
@require_service_jwt
def create_order():
    limit = _get_positive_int_env("ORDER_CREATE_RATE_LIMIT", 60)
    window = _get_positive_int_env("ORDER_CREATE_RATE_WINDOW_SECONDS", 60)
    allowed, retry_after = _enforce_rate_limit("create", limit, window)
    if not allowed:
        return _rate_limited_response(retry_after)

    data = request.get_json(silent=True)
    payload, error = validate_create_order_payload(data)
    if error:
        return jsonify({"error": error}), 400

    db = SessionLocal()
    try:
        order = create_order_record(
            db,
            user_id=payload["user_id"],
            product_ids=payload["product_ids"],
            total=payload["total"],
        )
        _invalidate_order_cache(order.id)
        response = jsonify({"order": order.to_dict()})
        return response, 201
    finally:
        db.close()


@app.route('/orders/<int:order_id>', methods=['GET'])
@require_service_jwt
def get_order(order_id):
    cached_order = cache_client.get_json(_order_cache_key(order_id))
    if isinstance(cached_order, dict):
        response = jsonify({"order": cached_order})
        response.headers["X-Cache"] = "HIT"
        return response

    db = SessionLocal()
    try:
        order = get_order_by_id(db, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        order_payload = order.to_dict()
        cache_client.set_json(_order_cache_key(order_id), order_payload, _order_cache_ttl())
        response = jsonify({"order": order_payload})
        response.headers["X-Cache"] = "MISS"
        return response
    finally:
        db.close()


@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
@require_service_jwt
def update_order_status(order_id):
    limit = _get_positive_int_env("ORDER_STATUS_RATE_LIMIT", 60)
    window = _get_positive_int_env("ORDER_STATUS_RATE_WINDOW_SECONDS", 60)
    allowed, retry_after = _enforce_rate_limit("status", limit, window)
    if not allowed:
        return _rate_limited_response(retry_after)

    db = SessionLocal()
    try:
        order = get_order_by_id(db, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        data = request.get_json(silent=True)
        payload, error = validate_status_payload(data)
        if error:
            return jsonify({"error": error}), 400

        order = update_order_status_record(db, order, payload["status"])
        _invalidate_order_cache(order.id)

        webhook_result = {}
        webhook_url = payload.get("webhook_url")
        if webhook_url:
            try:
                resp = requests.post(
                    webhook_url,
                    json={
                        "order_id": order.id,
                        "status": order.status,
                        "user_id": order.user_id,
                        "product_ids": order.to_dict()["product_ids"],
                        "total": order.total,
                        "updated_at": order.created_at.isoformat() + "Z",
                    },
                    timeout=5,
                )
                webhook_result = {"webhook_status": resp.status_code}
            except Exception as err:
                webhook_result = {"webhook_error": str(err)}

        return jsonify({"order": order.to_dict(), **webhook_result})
    finally:
        db.close()


if __name__ == '__main__':
    get_service_jwt_secret(os.environ)
    create_tables()
    app.run(host='0.0.0.0', port=7000)
