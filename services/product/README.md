## Inter-service authentication

All internal API calls require a JWT in the Authorization header:

- `Authorization: Bearer <token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)

Tokens are validated on every protected endpoint.
## Product Search

The GraphQL API exposes a `searchProducts` query:

```graphql
query {
	searchProducts(name: "shirt") {
		id
		name
		price
		category { name }
	}
}
```
## Product Posts

Product posts are modeled in `models.py` as `ProductPost`:
- `id`, `product_id`, `user_id`, `content`, `timestamp`

The GraphQL API exposes a `posts` query:

```graphql
query {
	posts {
		id
		product { name }
		user_id
		content
		timestamp
	}
}
```
## Models

Models are defined in `models.py` using SQLAlchemy:
- `Product`: id, name, description, price, category_id
- `Category`: id, name, description

For now, the GraphQL API uses in-memory demo data. Integrate with a real database and migrations for production.

## Migrations

To set up the database tables, use Alembic or Flask-Migrate (not yet included).
# ShopSocial Product Service
This is the Flask + GraphQL microservice for product catalog and posts.
## Development
- Entry point: `app.py`
- GraphQL endpoint: `/graphql`
- Schema defined in `schema.py`
## Running locally
1. Ensure the root `.venv` is activated and dependencies are installed via `uv`:
	```bash
	uv pip install flask graphene
	```
2. Run the service:
	```bash
	python services/product/app.py
## Dependencies

- flask
- graphene

All dependencies are managed in the root `.venv` using `uv` at the project root.
## Usage
Once running, you can test the GraphQL endpoint with:

```bash
curl -X POST -H "Content-Type: application/json" \
	--data '{"query": "{ hello }"}' \
	http://localhost:5000/graphql
```

You should receive:
```json
{"data":{"hello":"Hello, ShopSocial!"}}
```
# Product Service

Flask + GraphQL for product catalog and posts.