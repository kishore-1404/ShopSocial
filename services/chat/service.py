from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

import jwt
from sqlalchemy.orm import Session

from models import ChatMessage

MIN_SECRET_LENGTH = 32


class CacheClientProtocol(Protocol):
    def get_json(self, key: str) -> Any | None:
        ...

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> bool:
        ...

    def delete(self, key: str) -> None:
        ...

    def delete_prefix(self, key_prefix: str) -> None:
        ...


def get_service_jwt_secret(env: dict[str, str]) -> str:
    secret = env.get("SERVICE_JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"SERVICE_JWT_SECRET must be set and at least {MIN_SECRET_LENGTH} characters"
        )
    return secret


def extract_jwt_from_protocol_headers(protocol_headers: list[str]) -> Optional[str]:
    for proto in protocol_headers:
        for part in proto.split(","):
            token_part = part.strip()
            if token_part.startswith("jwt="):
                token = token_part[4:].strip()
                if token:
                    return token
    return None


def extract_jwt_from_authorization_header(authorization: str | None) -> Optional[str]:
    if authorization is None:
        return None
    value = authorization.strip()
    if not value.startswith("Bearer "):
        return None
    token = value.split(" ", 1)[1].strip()
    return token or None


def validate_service_jwt(token: str, secret: str) -> bool:
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except Exception:
        return False


def parse_json_payload(message: str) -> dict[str, Any]:
    data = json.loads(message)
    if not isinstance(data, dict):
        raise ValueError("Invalid message format")
    return data


def validate_join_payload(data: dict[str, Any]) -> str:
    if data.get("action") != "join":
        raise ValueError("Must join a product room first.")

    product_id = data.get("product_id")
    if not isinstance(product_id, int) or product_id <= 0:
        raise ValueError("product_id must be a positive integer")

    return str(product_id)


def validate_message_payload(data: dict[str, Any]) -> str:
    if data.get("action") != "message":
        raise ValueError("Invalid message format.")

    content = data.get("content")
    if not isinstance(content, str):
        raise ValueError("content must be a string")

    normalized = content.strip()
    if not normalized:
        raise ValueError("content cannot be empty")

    if len(normalized) > 1000:
        raise ValueError("content must be 1000 characters or fewer")

    return normalized


def serialize_chat_message(chat_message: ChatMessage) -> dict[str, str]:
    timestamp_iso = chat_message.timestamp.isoformat()
    if timestamp_iso.endswith("+00:00"):
        timestamp_iso = timestamp_iso[:-6] + "Z"
    elif not timestamp_iso.endswith("Z"):
        timestamp_iso = timestamp_iso + "Z"

    return {
        "room": chat_message.room_id,
        "from": chat_message.sender,
        "content": chat_message.content,
        "timestamp": timestamp_iso,
    }


def history_cache_key(room_id: str, limit: int) -> str:
    return f"chat:history:{room_id}:{limit}"


def history_cache_prefix(room_id: str) -> str:
    return f"chat:history:{room_id}:"


def fetch_recent_history(
    db: Session,
    room_id: str,
    limit: int = 50,
    cache_client: CacheClientProtocol | None = None,
    cache_ttl_seconds: int = 15,
) -> list[dict[str, str]]:
    cache_key = history_cache_key(room_id, limit)
    if cache_client is not None:
        cached = cache_client.get_json(cache_key)
        if isinstance(cached, list):
            return cached

    recent_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
        .all()
    )
    history = [serialize_chat_message(m) for m in reversed(recent_msgs)]

    if cache_client is not None:
        cache_client.set_json(cache_key, history, max(cache_ttl_seconds, 1))

    return history


def save_chat_message(
    db: Session,
    room_id: str,
    sender: str,
    content: str,
    cache_client: CacheClientProtocol | None = None,
) -> dict[str, str]:
    msg = ChatMessage(
        room_id=room_id,
        sender=sender,
        content=content,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(msg)
    db.commit()

    if cache_client is not None:
        cache_client.delete_prefix(history_cache_prefix(room_id))

    return serialize_chat_message(msg)