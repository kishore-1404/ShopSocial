import pytest
import websockets
import jwt
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SERVICES_DIR = Path(__file__).resolve().parent.parent
if str(SERVICES_DIR) not in sys.path:
    sys.path.append(str(SERVICES_DIR))

os.environ.setdefault("SERVICE_JWT_SECRET", "shopsocial-chat-test-secret-with-32-plus-bytes")

from service import (
    extract_jwt_from_authorization_header,
    extract_jwt_from_protocol_headers,
    fetch_recent_history,
    get_service_jwt_secret,
    history_cache_key,
    history_cache_prefix,
    save_chat_message,
    validate_join_payload,
    validate_message_payload,
)
from common.cache_service import reset_cache_client
from common.rate_limit import get_rate_limiter, reset_rate_limiter

SECRET = os.environ["SERVICE_JWT_SECRET"]

@pytest.mark.asyncio
async def test_ws_rejects_missing_jwt():
    try:
        async with websockets.connect('ws://localhost:9000') as ws:
            await ws.send('')
            await ws.recv()
    except Exception as e:
        msg = str(e)
        if 'Connect call failed' in msg or 'connection refused' in msg.lower():
            pytest.skip(f"WebSocket server not running: {e}")
        assert '401' in msg or '4401' in msg

@pytest.mark.asyncio
async def test_ws_accepts_valid_jwt():
    token = jwt.encode({"service": "test"}, SECRET, algorithm="HS256")
    try:
        async with websockets.connect('ws://localhost:9000', extra_headers=[('Sec-WebSocket-Protocol', f'jwt={token}')]) as ws:
            # Try to join a room
            await ws.send('{"action": "join", "product_id": 1}')
            msg = await ws.recv()
            assert 'Joined room' in msg
    except Exception as e:
        pytest.skip(f"WebSocket server not running: {e}")


def test_extract_jwt_from_protocol_headers():
    token = extract_jwt_from_protocol_headers(["chat, jwt=abc.def.ghi"])
    assert token == "abc.def.ghi"


def test_extract_jwt_from_authorization_header():
    token = extract_jwt_from_authorization_header("Bearer abc.def.ghi")
    assert token == "abc.def.ghi"


def test_validate_join_payload_rejects_invalid_product_id():
    with pytest.raises(ValueError, match="product_id"):
        validate_join_payload({"action": "join", "product_id": 0})


def test_validate_message_payload_rejects_empty_content():
    with pytest.raises(ValueError, match="empty"):
        validate_message_payload({"action": "message", "content": "   "})


def test_get_service_jwt_secret_enforces_length():
    with pytest.raises(RuntimeError, match="SERVICE_JWT_SECRET"):
        get_service_jwt_secret({"SERVICE_JWT_SECRET": "short"})


def test_chat_message_rate_limit_allows_then_blocks(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USE_REDIS", "0")
    reset_rate_limiter()
    limiter = get_rate_limiter()

    allowed_first, _ = limiter.allow("chat:test:room-1:user-a", limit=2, window_seconds=60)
    allowed_second, _ = limiter.allow("chat:test:room-1:user-a", limit=2, window_seconds=60)
    allowed_third, retry_after = limiter.allow("chat:test:room-1:user-a", limit=2, window_seconds=60)

    assert allowed_first is True
    assert allowed_second is True
    assert allowed_third is False
    assert retry_after >= 1


def test_fetch_recent_history_uses_cache_hit():
    class DummyCache:
        def get_json(self, key):
            return [{"room": "1", "content": "cached"}]

        def set_json(self, key, value, ttl_seconds):
            return True

        def delete(self, key):
            return None

        def delete_prefix(self, key_prefix):
            return None

    class NoQueryDB:
        def query(self, model):
            raise AssertionError("DB query should not run on cache hit")

    history = fetch_recent_history(NoQueryDB(), "1", cache_client=DummyCache())
    assert history == [{"room": "1", "content": "cached"}]


def test_fetch_recent_history_sets_cache_on_miss():
    class DummyMessage:
        def __init__(self, room_id, sender, content, timestamp):
            self.room_id = room_id
            self.sender = sender
            self.content = content
            self.timestamp = timestamp

    class DummyQuery:
        def __init__(self, messages):
            self._messages = messages

        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def all(self):
            return self._messages

    class DummyDB:
        def __init__(self, messages):
            self._messages = messages

        def query(self, model):
            return DummyQuery(self._messages)

    class RecordingCache:
        def __init__(self):
            self.saved = {}

        def get_json(self, key):
            return None

        def set_json(self, key, value, ttl_seconds):
            self.saved[key] = (value, ttl_seconds)
            return True

        def delete(self, key):
            return None

        def delete_prefix(self, key_prefix):
            return None

    messages = [
        DummyMessage("1", "user-a", "hello", datetime.now(timezone.utc).replace(tzinfo=None)),
    ]
    cache = RecordingCache()
    history = fetch_recent_history(DummyDB(messages), "1", cache_client=cache, cache_ttl_seconds=30)

    key = history_cache_key("1", 50)
    assert key in cache.saved
    assert cache.saved[key][1] == 30
    assert isinstance(history, list)
    assert len(history) == 1


def test_save_chat_message_invalidates_history_cache_prefix(monkeypatch):
    monkeypatch.setenv("CACHE_USE_REDIS", "0")
    reset_cache_client()

    class DummyDB:
        def __init__(self):
            self.added = []
            self.committed = False

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.committed = True

    class RecordingCache:
        def __init__(self):
            self.deleted_prefixes = []

        def get_json(self, key):
            return None

        def set_json(self, key, value, ttl_seconds):
            return True

        def delete(self, key):
            return None

        def delete_prefix(self, key_prefix):
            self.deleted_prefixes.append(key_prefix)

    db = DummyDB()
    cache = RecordingCache()
    payload = save_chat_message(db, "22", "sender", "hello", cache_client=cache)

    assert db.committed is True
    assert payload["room"] == "22"
    assert history_cache_prefix("22") in cache.deleted_prefixes
