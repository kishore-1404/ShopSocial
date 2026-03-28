
import asyncio
import websockets
import json
from collections import defaultdict

import os
import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
SERVICES_DIR = Path(__file__).resolve().parent.parent
if str(SERVICES_DIR) not in sys.path:
    sys.path.append(str(SERVICES_DIR))

from common.logging_service import bind_context, clear_context, configure_logging, get_logger
from common.cache_service import get_cache_client
from common.rate_limit import get_rate_limiter
from service import (
    extract_jwt_from_authorization_header,
    extract_jwt_from_protocol_headers,
    fetch_recent_history,
    get_service_jwt_secret,
    parse_json_payload,
    save_chat_message,
    validate_join_payload,
    validate_message_payload,
    validate_service_jwt,
)

configure_logging("chat")
logger = get_logger(__name__, "chat")
cache_client = get_cache_client()
rate_limiter = get_rate_limiter()


def _get_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _history_cache_ttl() -> int:
    return _get_positive_int_env("CHAT_HISTORY_CACHE_TTL", 15)


PORT = 9000

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



# room_id (product_id) -> set of websockets
rooms = defaultdict(set)


def _request_header_values(websocket, header_name: str) -> list[str]:
    request_headers = getattr(websocket, "request_headers", None)
    if request_headers is not None:
        values = request_headers.get_all(header_name)
        return list(values) if values else []

    request = getattr(websocket, "request", None)
    if request is not None and getattr(request, "headers", None) is not None:
        values = request.headers.get_all(header_name)
        return list(values) if values else []

    return []


def _request_header_value(websocket, header_name: str) -> str | None:
    values = _request_header_values(websocket, header_name)
    return values[0] if values else None

async def handler(websocket, path=None):
    db = SessionLocal()
    service_secret = get_service_jwt_secret(os.environ)

    # Expect JWT in Sec-WebSocket-Protocol header as 'jwt=<token>'
    jwt_token = extract_jwt_from_protocol_headers(
        _request_header_values(websocket, "Sec-WebSocket-Protocol")
    )
    if not jwt_token:
        jwt_token = extract_jwt_from_authorization_header(
            _request_header_value(websocket, "Authorization")
        )
    if not jwt_token:
        await websocket.close(code=4401, reason="Missing JWT")
        logger.warning("missing_jwt", extra={"event": "auth_failed"})
        return
    if not validate_service_jwt(jwt_token, service_secret):
        await websocket.close(code=4401, reason="Invalid JWT")
        logger.warning("invalid_jwt", extra={"event": "auth_failed"})
        return

    room_id = None
    try:
        bind_context(connection_id=str(uuid.uuid4()))
        # Expect first message to be a join message: {"action": "join", "product_id": 123}
        join_msg = await websocket.recv()
        join_data = parse_json_payload(join_msg)
        try:
            room_id = validate_join_payload(join_data)
        except ValueError as err:
            await websocket.send(json.dumps({"error": str(err)}))
            logger.warning("invalid_join_payload", extra={"event": "validation_failed"})
            return

        rooms[room_id].add(websocket)
        bind_context(room_id=room_id)
        logger.info("joined_room", extra={"event": "joined_room"})
        await websocket.send(json.dumps({"info": f"Joined room {room_id}"}))

        # Send recent chat history (last 50 messages) from DB
        msgs = fetch_recent_history(
            db,
            room_id,
            cache_client=cache_client,
            cache_ttl_seconds=_history_cache_ttl(),
        )
        if msgs:
            await websocket.send(json.dumps({"history": msgs}))

        async for message in websocket:
            try:
                data = parse_json_payload(message)
                if data.get("action") == "message":
                    message_limit = _get_positive_int_env("CHAT_MESSAGE_RATE_LIMIT", 120)
                    message_window = _get_positive_int_env("CHAT_MESSAGE_RATE_WINDOW_SECONDS", 60)
                    allowed, retry_after = rate_limiter.allow(
                        f"chat:message:{room_id}:{websocket.remote_address}",
                        message_limit,
                        message_window,
                    )
                    if not allowed:
                        logger.warning("rate_limit_exceeded", extra={"event": "rate_limited"})
                        await websocket.send(
                            json.dumps(
                                {
                                    "error": "Rate limit exceeded",
                                    "retry_after": retry_after,
                                }
                            )
                        )
                        continue

                    content = validate_message_payload(data)
                    msg_dict = save_chat_message(
                        db,
                        room_id=room_id,
                        sender=str(websocket.remote_address),
                        content=content,
                        cache_client=cache_client,
                    )
                    logger.info("broadcast_message", extra={"event": "broadcast_message"})
                    # Broadcast to all in the same room
                    for conn in list(rooms[room_id]):
                        if conn.open:
                            try:
                                await conn.send(json.dumps(msg_dict))
                            except Exception as send_err:
                                logger.error("send_error", extra={"event": "send_error"})
                elif data.get("action") == "history":
                    # Client requests recent history from DB
                    msgs = fetch_recent_history(
                        db,
                        room_id,
                        cache_client=cache_client,
                        cache_ttl_seconds=_history_cache_ttl(),
                    )
                    await websocket.send(json.dumps({"history": msgs}))
                else:
                    await websocket.send(json.dumps({"error": "Invalid message format."}))
            except ValueError as err:
                logger.warning("message_validation_error", extra={"event": "validation_failed"})
                await websocket.send(json.dumps({"error": str(err)}))
            except Exception as err:
                logger.exception("message_handling_error", extra={"event": "message_handling_error"})
                await websocket.send(json.dumps({"error": "Invalid message format."}))
    except websockets.ConnectionClosed:
        logger.info("client_disconnected", extra={"event": "client_disconnected"})
    except Exception:
        logger.exception("unexpected_handler_error", extra={"event": "unexpected_error"})
    finally:
        db.close()
        if room_id and websocket in rooms[room_id]:
            rooms[room_id].remove(websocket)
            if not rooms[room_id]:
                del rooms[room_id]
        clear_context()


async def main():
    get_service_jwt_secret(os.environ)
    create_tables()
    async with websockets.serve(handler, "0.0.0.0", PORT):
        logger.info("chat_server_started", extra={"event": "startup", "port": PORT})
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
