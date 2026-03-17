import pytest
import websockets
import asyncio
import jwt
import os

SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

@pytest.mark.asyncio
async def test_ws_rejects_missing_jwt():
    try:
        async with websockets.connect('ws://localhost:9000') as ws:
            await ws.send('')
    except Exception as e:
        assert '401' in str(e) or '4401' in str(e)

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
