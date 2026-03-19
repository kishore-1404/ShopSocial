
import asyncio
import websockets
import logging
import json
from collections import defaultdict
from datetime import datetime

import os
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, ChatMessage

logging.basicConfig(level=logging.INFO)


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

SERVICE_JWT_SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

async def handler(websocket, path):
    db = SessionLocal()
    # Expect JWT in Sec-WebSocket-Protocol header as 'jwt=<token>'
    jwt_token = None
    for proto in websocket.request_headers.get_all('Sec-WebSocket-Protocol', []):
        if proto.startswith('jwt='):
            jwt_token = proto[4:]
            break
    if not jwt_token:
        await websocket.close(code=4401, reason="Missing JWT")
        return
    try:
        jwt.decode(jwt_token, SERVICE_JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        await websocket.close(code=4401, reason=f"Invalid JWT: {str(e)}")
        return
    room_id = None
    try:
        # Expect first message to be a join message: {"action": "join", "product_id": 123}
        join_msg = await websocket.recv()
        join_data = json.loads(join_msg)
        if join_data.get("action") != "join" or "product_id" not in join_data:
            await websocket.send(json.dumps({"error": "Must join a product room first."}))
            return

        room_id = str(join_data["product_id"])
        rooms[room_id].add(websocket)
        logging.info(f"Client {websocket.remote_address} joined room {room_id}")
        await websocket.send(json.dumps({"info": f"Joined room {room_id}"}))

        # Send recent chat history (last 50 messages) from DB
        recent_msgs = db.query(ChatMessage).filter(ChatMessage.room_id == room_id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
        if recent_msgs:
            # Reverse to chronological order
            msgs = [
                {
                    "room": m.room_id,
                    "from": m.sender,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() + "Z"
                } for m in reversed(recent_msgs)
            ]
            await websocket.send(json.dumps({"history": msgs}))

        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("action") == "message" and "content" in data:
                    msg = ChatMessage(
                        room_id=room_id,
                        sender=str(websocket.remote_address),
                        content=data["content"],
                        timestamp=datetime.utcnow()
                    )
                    db.add(msg)
                    db.commit()
                    # Prepare broadcast dict
                    msg_dict = {
                        "room": msg.room_id,
                        "from": msg.sender,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() + "Z"
                    }
                    logging.info(f"Broadcasting message in room {room_id}: {msg_dict}")
                    # Broadcast to all in the same room
                    for conn in list(rooms[room_id]):
                        if conn.open:
                            try:
                                await conn.send(json.dumps(msg_dict))
                            except Exception as send_err:
                                logging.error(f"Send error: {send_err}")
                elif data.get("action") == "history":
                    # Client requests recent history from DB
                    recent_msgs = db.query(ChatMessage).filter(ChatMessage.room_id == room_id).order_by(ChatMessage.timestamp.desc()).limit(50).all()
                    msgs = [
                        {
                            "room": m.room_id,
                            "from": m.sender,
                            "content": m.content,
                            "timestamp": m.timestamp.isoformat() + "Z"
                        } for m in reversed(recent_msgs)
                    ]
                    await websocket.send(json.dumps({"history": msgs}))
                else:
                    await websocket.send(json.dumps({"error": "Invalid message format."}))
            except Exception as e:
                logging.error(f"Message handling error: {e}")
                await websocket.send(json.dumps({"error": str(e)}))
    except websockets.ConnectionClosed:
        logging.info(f"Client disconnected: {websocket.remote_address}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        db.close()
        if room_id and websocket in rooms[room_id]:
            rooms[room_id].remove(websocket)
            if not rooms[room_id]:
                del rooms[room_id]


async def main():
    create_tables()
    async with websockets.serve(handler, "0.0.0.0", PORT):
        logging.info(f"WebSocket server started on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
