# Chat Service

WebSocket-based chat microservice for ShopSocial. Enables real-time chat in product rooms.

## Features
- Real-time chat rooms per product (room = product_id)
- Broadcast messages to all clients in a room
- Chat history (last 50 messages on join/request)
- JWT-based inter-service authentication (HS256)

## Protocol
- **WebSocket header:** `Sec-WebSocket-Protocol: jwt=<token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)
- Tokens are validated on every connection.

## Message Flows
1. **Join a room:**
	```json
	{"action": "join", "product_id": 123}
	```
2. **Send a message:**
	```json
	{"action": "message", "content": "Hello!"}
	```
3. **Receive broadcast:**
	```json
	{"room": "123", "from": "<client>", "content": "Hello!", "timestamp": "..."}
	```
4. **Receive history on join:**
	```json
	{"history": [ ... ]}
	```
5. **Request history:**
	```json
	{"action": "history"}
	```
	Response:
	```json
	{"history": [ ... ]}
	```

## Setup & Running Locally
1. Activate the root `.venv` and install dependencies:
	```sh
	uv pip install websockets
	```
2. Run the service:
	```sh
	python services/chat/app.py
	```

## Notes
- Entry point: `app.py`
- Runs on port 9000
- All clients must join a product room before sending messages
- Only clients in the same room receive each other's messages
- On join, server sends last 50 messages as chat history

## Next Steps
- Add user authentication and presence
- Persist chat history

---
*This README was auto-generated and merges all useful information from previous documentation.*