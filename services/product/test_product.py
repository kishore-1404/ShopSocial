import os
import uuid

import jwt
import pytest

os.environ.setdefault("SERVICE_JWT_SECRET", "shopsocial-product-test-secret-with-32-plus-bytes")

from app import SessionLocal, create_app
from common.cache_service import reset_cache_client
from common.rate_limit import reset_rate_limiter
from models import Category, Product, ProductPost

SECRET = os.environ["SERVICE_JWT_SECRET"]

def make_jwt():
    return jwt.encode({"service": "test"}, SECRET, algorithm="HS256")

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_shared_rate_limiter(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USE_REDIS", "0")
    monkeypatch.setenv("CACHE_USE_REDIS", "0")
    reset_rate_limiter()
    reset_cache_client()
    yield
    reset_rate_limiter()
    reset_cache_client()

def auth_header():
    return {"Authorization": f"Bearer {make_jwt()}"}

@pytest.fixture
def seed_data():
    db = SessionLocal()
    token = uuid.uuid4().hex[:8]
    ids = {}

    try:
        category = Category(name=f"Electronics-{token}", description="Devices")
        db.add(category)
        db.flush()

        phone = Product(name=f"Phone-{token}", description="Smartphone", price=699.0, category_id=category.id)
        watch = Product(name=f"Watch-{token}", description="Wearable", price=199.0, category_id=category.id)
        db.add_all([phone, watch])
        db.flush()

        post = ProductPost(
            product_id=phone.id,
            user_id=101,
            content="Great product",
            timestamp="2026-03-28T10:00:00Z",
        )
        db.add(post)
        db.commit()

        ids = {
            "category_id": category.id,
            "phone_id": phone.id,
            "watch_id": watch.id,
            "post_id": post.id,
            "token": token,
        }

        yield ids
    finally:
        db.rollback()
        if ids:
            db.query(ProductPost).filter(ProductPost.id == ids["post_id"]).delete(synchronize_session=False)
            db.query(Product).filter(Product.id.in_([ids["phone_id"], ids["watch_id"]])).delete(synchronize_session=False)
            db.query(Category).filter(Category.id == ids["category_id"]).delete(synchronize_session=False)
            db.commit()
        db.close()
        SessionLocal.remove()


def test_hello_query(client):
    query = '{ hello }'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["hello"] == "Hello, ShopSocial!"


def test_product_healthz_endpoint(client):
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.get_json() == {"service": "product", "status": "ok"}


def test_graphql_requires_authorization(client):
    query = '{ hello }'
    resp = client.post('/graphql', json={"query": query})
    assert resp.status_code == 401


def test_graphql_rejects_invalid_token(client):
    query = '{ hello }'
    resp = client.post(
        '/graphql',
        json={"query": query},
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid token"


def test_graphql_rejects_missing_query_field(client):
    resp = client.post('/graphql', json={}, headers=auth_header())
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Field `query` is required"


def test_create_app_requires_strong_jwt_secret(monkeypatch):
    monkeypatch.setenv("SERVICE_JWT_SECRET", "short")
    with pytest.raises(RuntimeError, match="SERVICE_JWT_SECRET"):
        create_app()


def test_products_query_returns_seeded_products(client, seed_data):
    query = '{ products { id name price } }'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert resp.status_code == 200
    data = resp.get_json()["data"]["products"]
    names = {item["name"] for item in data}
    assert f"Phone-{seed_data['token']}" in names
    assert f"Watch-{seed_data['token']}" in names


def test_search_products_by_name(client, seed_data):
    query = f'{{ searchProducts(name: "Phone-{seed_data["token"]}") {{ name }} }}'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert resp.status_code == 200
    data = resp.get_json()["data"]["searchProducts"]
    assert len(data) >= 1
    assert all(seed_data["token"] in item["name"] for item in data)


def test_search_products_rejects_invalid_category_id(client):
    query = '{ searchProducts(categoryId: 0) { id name } }'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert resp.status_code == 200
    payload = resp.get_json()
    assert "errors" in payload
    assert any("categoryId must be a positive integer" in msg for msg in payload["errors"])


def test_posts_query_returns_product_posts(client, seed_data):
    query = '{ posts { content userId product { name } } }'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert resp.status_code == 200
    data = resp.get_json()["data"]["posts"]
    assert any(item["content"] == "Great product" for item in data)


def test_graphql_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setenv("PRODUCT_GRAPHQL_RATE_LIMIT", "2")
    monkeypatch.setenv("PRODUCT_GRAPHQL_RATE_WINDOW_SECONDS", "60")

    query = '{ hello }'
    first = client.post('/graphql', json={"query": query}, headers=auth_header())
    second = client.post('/graphql', json={"query": query}, headers=auth_header())
    third = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.get_json()["error"] == "Rate limit exceeded"


def test_graphql_read_query_uses_response_cache(client):
    query = '{ hello }'

    first = client.post('/graphql', json={"query": query}, headers=auth_header())
    second = client.post('/graphql', json={"query": query}, headers=auth_header())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    assert second.headers.get("X-Cache") == "HIT"
    assert first.get_json() == second.get_json()
