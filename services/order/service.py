from __future__ import annotations

from typing import Any, Optional

import jwt
from sqlalchemy.orm import Session

from models import Order

VALID_STATUSES = {"pending", "paid", "shipped", "completed", "cancelled"}
MIN_SECRET_LENGTH = 32


def get_service_jwt_secret(env: dict[str, str]) -> str:
    secret = env.get("SERVICE_JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"SERVICE_JWT_SECRET must be set and at least {MIN_SECRET_LENGTH} characters"
        )
    return secret


def validate_service_jwt(token: str, secret: str) -> bool:
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except Exception:
        return False


def validate_create_order_payload(data: Any) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    if not isinstance(data, dict):
        return None, "Invalid JSON payload"

    user_id = data.get("user_id")
    product_ids = data.get("product_ids")
    total = data.get("total")

    if not isinstance(user_id, int) or user_id <= 0:
        return None, "user_id must be a positive integer"
    if not isinstance(product_ids, list) or len(product_ids) == 0:
        return None, "product_ids must be a non-empty list"
    if not all(isinstance(pid, int) and pid > 0 for pid in product_ids):
        return None, "product_ids must contain positive integers"
    if not isinstance(total, (int, float)) or total <= 0:
        return None, "total must be a positive number"

    return {
        "user_id": user_id,
        "product_ids": product_ids,
        "total": float(total),
    }, None


def validate_status_payload(data: Any) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    if not isinstance(data, dict):
        return None, "Invalid JSON payload"

    status = data.get("status")
    webhook_url = data.get("webhook_url")

    if status not in VALID_STATUSES:
        return None, "Invalid status"
    if webhook_url is not None and (not isinstance(webhook_url, str) or not webhook_url.strip()):
        return None, "webhook_url must be a non-empty string when provided"

    return {"status": status, "webhook_url": webhook_url}, None


def create_order(db: Session, user_id: int, product_ids: list[int], total: float) -> Order:
    order = Order.from_data(user_id, product_ids, total)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def update_order_status(db: Session, order: Order, status: str) -> Order:
    order.status = status
    db.commit()
    db.refresh(order)
    return order