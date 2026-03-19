
import asyncio
import websockets
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

async def echo(websocket, path):
    async for message in websocket:
        await websocket.send(f"Echo: {message}")

async def main():
    async with websockets.serve(echo, "0.0.0.0", 9000):
        print("Chat server started on ws://0.0.0.0:9000")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
