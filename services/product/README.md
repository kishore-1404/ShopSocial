# Product Service


Flask + GraphQL microservice for product catalog and product posts in ShopSocial.

## Architecture

- Uses SQLAlchemy ORM with a persistent Postgres database (see docker-compose.yml).
- All data access is via the database; in-memory lists are no longer used.
- Models are defined in models.py; DB session is managed in app.py and injected into GraphQL context.

## Features
- Product catalog (CRUD via GraphQL)
- Product categories
- Product posts (user-generated content)
- Product search (by name, category)
- Inter-service authentication (JWT, HS256)

## API
- **GraphQL endpoint:** `/graphql` (POST)
- **Entry point:** `app.py`
- **Schema:** `schema.py`

### Example Queries
#### Product Search
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
#### Product Posts
```graphql
query {
	posts {
		id
		product { name }
		userId
		content
		timestamp
	}
}
```

## Models
- **Product**: id, name, description, price, category_id
- **Category**: id, name, description
- **ProductPost**: id, product_id, user_id, content, timestamp

Models are defined in `models.py` using SQLAlchemy. The current API uses in-memory demo data; integrate a real DB for production.

## Authentication
All internal API calls require a JWT in the Authorization header:
- `Authorization: Bearer <token>`
- Secret: from `SERVICE_JWT_SECRET` env var (HS256)
Tokens are validated on every protected endpoint.

## Setup & Running Locally
1. Activate the root `.venv` and install dependencies:
	 ```sh
	 uv pip install flask graphene
	 ```
2. Run the service:
	 ```sh
	 python services/product/app.py
	 ```

## Usage
Test the GraphQL endpoint:
```sh
curl -X POST -H "Content-Type: application/json" \
	--data '{"query": "{ hello }"}' \
	http://localhost:5000/graphql
```
Response:
```json
{"data":{"hello":"Hello, ShopSocial!"}}
```

## Migrations
To set up DB tables, use Alembic or Flask-Migrate (not yet included).

---
*This README was auto-generated and merges all useful information from previous documentation.*