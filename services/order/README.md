## Inter-service authentication

All internal API calls require a JWT in the Authorization header:

- `Authorization: Bearer <token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)

Tokens are validated on every protected endpoint.
# ShopSocial Order Service

This is the order processing microservice for ShopSocial.

## Development

- Entry point: `app.py`
- Runs on port 7000
- Uses Flask (Python)

## Running locally

1. Ensure the root `.venv` is activated and dependencies are installed via `uv`.
2. Install the required package:
	 ```bash
	 uv pip install flask
	 ```
3. Run the service:
	 ```bash
	 python services/order/app.py
	 ```

- Health check endpoint at `/`
- Create order: `POST /orders` (fields: user_id, product_ids, total)
- Get order: `GET /orders/<order_id>`

- Update order status: `PATCH /orders/<order_id>/status` (fields: status, optional webhook_url)
### Example: Update order status with webhook
```bash
curl -X PATCH -H "Content-Type: application/json" \
	-d '{"status": "shipped", "webhook_url": "http://example.com/webhook"}' \
	http://localhost:7000/orders/1/status
```

- Process order in background: `POST /orders/<order_id>/process`

## Celery Worker

Start the Celery worker (requires Redis running at `redis://redis:6379/0`):
```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

### Example: Trigger background processing
```bash
curl -X POST http://localhost:7000/orders/1/process
```

### Example: Create order
```bash
curl -X POST -H "Content-Type: application/json" \
	-d '{"user_id": 1, "product_ids": [101,102], "total": 49.99}' \
	http://localhost:7000/orders
```

### Example: Update order status
```bash
curl -X PATCH -H "Content-Type: application/json" \
	-d '{"status": "paid"}' \
	http://localhost:7000/orders/1/status
```

## Next steps
- Add Celery for background jobs
- Add webhook notifications