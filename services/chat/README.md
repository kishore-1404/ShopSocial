## Inter-service authentication

All internal WebSocket connections require a JWT in the Sec-WebSocket-Protocol header:

- `Sec-WebSocket-Protocol: jwt=<token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)

Tokens are validated on every connection.
# ShopSocial Chat Service

This is the WebSocket-based chat microservice for ShopSocial.

## Development

- Entry point: `app.py`
- Runs on port 9000
- Uses the `websockets` library (Python)

## Running locally

1. Ensure the root `.venv` is activated and dependencies are installed via `uv`.
2. Install the required package:
	 ```bash
	 uv pip install websockets
	 ```
3. Run the service:
	 ```bash
	 python services/chat/app.py
	 ```

- Accepts WebSocket connections
- Clients must join a product room by sending:
	```json
	{"action": "join", "product_id": 123}
	```
- After joining, send messages to the room:
	```json
	{"action": "message", "content": "Hello!"}
	```
- Messages are broadcast only to clients in the same product room.

- On join, the server sends the last 50 messages as chat history:
	```json
	{"history": [ ... ]}
	```
- Clients can request history at any time:
	```json
	{"action": "history"}
	```
	The server responds with:
	```json
	{"history": [ ... ]}
	```

## Next steps
- Add user authentication and presence
- Persist chat history