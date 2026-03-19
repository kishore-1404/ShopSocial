
from flask import Flask, jsonify, request

from models import Order, Base
from typing import List
import threading
from celery_worker import process_order
import requests
import os
import jwt
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


app = Flask(__name__)
SERVICE_JWT_SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

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
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            jwt.decode(token, SERVICE_JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated




@app.route('/orders/<int:order_id>/process', methods=['POST'])
@require_service_jwt
def process_order_bg(order_id):
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404
    task = process_order.delay(order_id)
    db.close()
    return jsonify({"task_id": task.id, "status": "processing"})



@app.route('/')
def index():
    return jsonify({"service": "order", "status": "ok"})


@app.route('/orders', methods=['POST'])
@require_service_jwt
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    product_ids = data.get('product_ids')
    total = data.get('total')
    if not user_id or not product_ids or not total:
        return jsonify({"error": "Missing required fields"}), 400
    db = SessionLocal()
    order = Order.from_data(user_id, product_ids, total)
    db.add(order)
    db.commit()
    db.refresh(order)
    result = order.to_dict()
    db.close()
    return jsonify({"order": result}), 201


@app.route('/orders/<int:order_id>', methods=['GET'])
@require_service_jwt
def get_order(order_id):
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404
    result = order.to_dict()
    db.close()
    return jsonify({"order": result})


@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
@require_service_jwt
def update_order_status(order_id):
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404
    data = request.get_json()
    status = data.get('status')
    webhook_url = data.get('webhook_url')
    valid_statuses = {'pending', 'paid', 'shipped', 'completed', 'cancelled'}
    if status not in valid_statuses:
        db.close()
        return jsonify({"error": "Invalid status"}), 400
    order.status = status
    db.commit()
    # Send webhook notification if URL provided
    if webhook_url:
        try:
            resp = requests.post(webhook_url, json={
                "order_id": order.id,
                "status": order.status,
                "user_id": order.user_id,
                "product_ids": order.product_ids,
                "total": order.total,
                "updated_at": order.created_at
            }, timeout=5)
            webhook_result = {"webhook_status": resp.status_code}
        except Exception as e:
            webhook_result = {"webhook_error": str(e)}
    else:
        webhook_result = {}
    result = order.to_dict()
    db.close()
    return jsonify({"order": result, **webhook_result})


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=7000)
