
from flask import Flask, jsonify, request
from models import Order, OrderStatus
from typing import List
import threading
from celery_worker import process_order
import requests
import os
import jwt
from functools import wraps

app = Flask(__name__)
import os
import jwt
from functools import wraps
SERVICE_JWT_SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

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

# In-memory order store (id -> Order)
orders = {}
order_id_counter = 1
lock = threading.Lock()

@app.route('/orders/<int:order_id>/process', methods=['POST'])
@require_service_jwt
def process_order_bg(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    task = process_order.delay(order_id)
    return jsonify({"task_id": task.id, "status": "processing"})


@app.route('/')
def index():
    return jsonify({"service": "order", "status": "ok"})

@app.route('/orders', methods=['POST'])
@require_service_jwt
def create_order():
    global order_id_counter
    data = request.get_json()
    user_id = data.get('user_id')
    product_ids = data.get('product_ids')
    total = data.get('total')
    if not user_id or not product_ids or not total:
        return jsonify({"error": "Missing required fields"}), 400
    with lock:
        oid = order_id_counter
        order_id_counter += 1
        order = Order(id=oid, user_id=user_id, product_ids=product_ids, total=total)
        orders[oid] = order
    return jsonify({"order": order.__dict__}), 201

@app.route('/orders/<int:order_id>', methods=['GET'])
@require_service_jwt
def get_order(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"order": order.__dict__})

@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
@require_service_jwt
def update_order_status(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    data = request.get_json()
    status = data.get('status')
    webhook_url = data.get('webhook_url')
    if status not in OrderStatus._value2member_map_:
        return jsonify({"error": "Invalid status"}), 400
    order.status = OrderStatus(status)
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
    return jsonify({"order": order.__dict__, **webhook_result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
