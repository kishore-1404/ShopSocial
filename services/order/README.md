## Inter-service authentication

All internal API calls require a JWT in the Authorization header:

- `Authorization: Bearer <token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)

Tokens are validated on every protected endpoint.
# Order Service


Flask microservice for order processing in ShopSocial. Handles order creation, status updates, and background processing with Celery.

## Architecture

- Uses SQLAlchemy ORM with a persistent Postgres database (see docker-compose.yml).
- All order data is stored in the database and loaded on request.
- Models are defined in models.py; DB session is managed in app.py.

## Features
- Create, retrieve, and update orders
- Order status lifecycle (pending, paid, shipped, completed, cancelled)
- Background order processing (Celery + Redis)
- Webhook notifications on status update
- JWT-based inter-service authentication (HS256)

## API Endpoints
| Method | Endpoint                        | Description                        | Auth Required |
|--------|----------------------------------|------------------------------------|---------------|
| POST   | /orders                         | Create order                       | Yes           |
| GET    | /orders/<order_id>              | Get order by ID                    | Yes           |
| PATCH  | /orders/<order_id>/status       | Update order status (+webhook)     | Yes           |
| POST   | /orders/<order_id>/process      | Process order in background        | Yes           |
| GET    | /                              | Health check                       | No            |

## Models
- **Order**: id, user_id, product_ids, total, status, created_at
- **OrderStatus**: pending, paid, shipped, completed, cancelled

## Authentication
All internal API calls require a JWT in the Authorization header:
- `Authorization: Bearer <token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)
Tokens are validated on every protected endpoint.

## Setup & Running Locally
1. Activate the root `.venv` and install dependencies:
	 ```sh
	 uv pip install flask celery redis
	 ```
2. Start Redis (see infrastructure/redis.conf).
3. Run the service:
	 ```sh
	 python services/order/app.py
	 ```
4. Start the Celery worker:
	 ```sh
	 celery -A celery_worker.celery_app worker --loglevel=info
	 ```

## Usage Examples
### Create order
```sh
curl -X POST -H "Content-Type: application/json" \
	-d '{"user_id": 1, "product_ids": [101,102], "total": 49.99}' \
	http://localhost:7000/orders
```
### Update order status
```sh
curl -X PATCH -H "Content-Type: application/json" \
	-d '{"status": "paid"}' \
	http://localhost:7000/orders/1/status
```
### Update order status with webhook
```sh
curl -X PATCH -H "Content-Type: application/json" \
	-d '{"status": "shipped", "webhook_url": "http://example.com/webhook"}' \
	http://localhost:7000/orders/1/status
```
### Trigger background processing
```sh
curl -X POST http://localhost:7000/orders/1/process
```

## Next Steps
- Integrate persistent DB for orders
- Expand webhook/event support

---
*This README was auto-generated and merges all useful information from previous documentation.*