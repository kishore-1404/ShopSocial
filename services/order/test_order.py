import pytest
from app import app, orders, order_id_counter
import jwt
import os

SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

def make_jwt():
    return jwt.encode({"service": "test"}, SECRET, algorithm="HS256")

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def auth_header():
    return {"Authorization": f"Bearer {make_jwt()}"}

def test_health(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert rv.get_json()["service"] == "order"

def test_create_and_get_order(client):
    orders.clear()
    global order_id_counter
    order_id_counter = 1
    resp = client.post('/orders', json={"user_id": 1, "product_ids": [1], "total": 10.0}, headers=auth_header())
    assert resp.status_code == 201
    order = resp.get_json()["order"]
    oid = order["id"]
    resp2 = client.get(f'/orders/{oid}', headers=auth_header())
    assert resp2.status_code == 200
    assert resp2.get_json()["order"]["user_id"] == 1
