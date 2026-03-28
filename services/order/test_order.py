import os
import importlib

import jwt
import pytest

os.environ.setdefault("SERVICE_JWT_SECRET", "shopsocial-order-test-secret-with-32-plus-bytes")

from app import SessionLocal, app, create_tables
from common.cache_service import reset_cache_client
from common.rate_limit import reset_rate_limiter
from models import Order


SECRET = os.environ["SERVICE_JWT_SECRET"]


def make_jwt():
    return jwt.encode({"service": "test"}, SECRET, algorithm="HS256")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    create_tables()
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_shared_rate_limiter(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USE_REDIS", "0")
    monkeypatch.setenv("CACHE_USE_REDIS", "0")
    reset_rate_limiter()
    reset_cache_client()
    yield
    reset_rate_limiter()
    reset_cache_client()


@pytest.fixture(autouse=True)
def cleanup_orders_table():
    db = SessionLocal()
    try:
        db.query(Order).delete(synchronize_session=False)
        db.commit()
        yield
    finally:
        db.query(Order).delete(synchronize_session=False)
        db.commit()
        db.close()
        SessionLocal.remove()


def auth_header():
    return {"Authorization": f"Bearer {make_jwt()}"}


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["service"] == "order"


def test_create_and_get_order(client):
    create_response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1, 2], "total": 10.0},
        headers=auth_header(),
    )
    assert create_response.status_code == 201

    created = create_response.get_json()["order"]
    order_id = created["id"]

    get_response = client.get(f"/orders/{order_id}", headers=auth_header())
    assert get_response.status_code == 200
    fetched = get_response.get_json()["order"]
    assert fetched["user_id"] == 1
    assert fetched["product_ids"] == [1, 2]


def test_create_order_rejects_invalid_payload(client):
    response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [], "total": 10.0},
        headers=auth_header(),
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "product_ids must be a non-empty list"


def test_create_order_requires_auth(client):
    response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1], "total": 10.0},
    )
    assert response.status_code == 401


def test_update_status_rejects_invalid_status(client):
    create_response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1], "total": 10.0},
        headers=auth_header(),
    )
    order_id = create_response.get_json()["order"]["id"]

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "unknown"},
        headers=auth_header(),
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid status"


def test_update_status_success(client):
    create_response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1], "total": 10.0},
        headers=auth_header(),
    )
    order_id = create_response.get_json()["order"]["id"]

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "paid"},
        headers=auth_header(),
    )
    assert response.status_code == 200
    assert response.get_json()["order"]["status"] == "paid"


def test_process_order_not_found(client):
    response = client.post("/orders/999/process", headers=auth_header())
    assert response.status_code == 404
    assert response.get_json()["error"] == "Order not found"


def test_celery_worker_uses_env_config(monkeypatch):
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6380/5")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6381/6")

    import celery_worker

    reloaded = importlib.reload(celery_worker)
    assert reloaded.CELERY_BROKER_URL == "redis://localhost:6380/5"
    assert reloaded.CELERY_RESULT_BACKEND == "redis://localhost:6381/6"


def test_create_order_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setenv("ORDER_CREATE_RATE_LIMIT", "1")
    monkeypatch.setenv("ORDER_CREATE_RATE_WINDOW_SECONDS", "60")

    first = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1], "total": 10.0},
        headers=auth_header(),
    )
    second = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [2], "total": 15.0},
        headers=auth_header(),
    )

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.get_json()["error"] == "Rate limit exceeded"


def test_get_order_uses_cache_on_second_read(client):
    create_response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1, 2], "total": 10.0},
        headers=auth_header(),
    )
    order_id = create_response.get_json()["order"]["id"]

    first = client.get(f"/orders/{order_id}", headers=auth_header())
    second = client.get(f"/orders/{order_id}", headers=auth_header())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    assert second.headers.get("X-Cache") == "HIT"
    assert first.get_json() == second.get_json()


def test_order_cache_invalidated_after_status_update(client):
    create_response = client.post(
        "/orders",
        json={"user_id": 1, "product_ids": [1], "total": 10.0},
        headers=auth_header(),
    )
    order_id = create_response.get_json()["order"]["id"]

    seed = client.get(f"/orders/{order_id}", headers=auth_header())
    cached = client.get(f"/orders/{order_id}", headers=auth_header())
    assert seed.headers.get("X-Cache") == "MISS"
    assert cached.headers.get("X-Cache") == "HIT"

    update_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "paid"},
        headers=auth_header(),
    )
    assert update_response.status_code == 200

    after_update = client.get(f"/orders/{order_id}", headers=auth_header())
    assert after_update.status_code == 200
    assert after_update.headers.get("X-Cache") == "MISS"
    assert after_update.get_json()["order"]["status"] == "paid"
