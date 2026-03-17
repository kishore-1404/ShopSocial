import pytest
from app import create_app
import jwt
import os

SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

def make_jwt():
    return jwt.encode({"service": "test"}, SECRET, algorithm="HS256")

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def auth_header():
    return {"Authorization": f"Bearer {make_jwt()}"}

def test_hello_query(client):
    query = '{ hello }'
    resp = client.post('/graphql', json={"query": query}, headers=auth_header())
    assert resp.status_code == 200
    assert resp.get_json()["data"]["hello"] == "Hello, ShopSocial!"
