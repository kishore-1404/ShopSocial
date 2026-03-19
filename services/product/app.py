
from flask import Flask, request, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import os
import jwt
from functools import wraps

SERVICE_JWT_SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

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

def require_service_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            jwt.decode(token, SERVICE_JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    create_tables()

    from schema import schema  # Import here to avoid circular import

    @app.route('/graphql', methods=['POST'])
    @require_service_jwt
    def graphql_server():
        data = request.get_json()
        # Pass DB session in context
        db = SessionLocal()
        try:
            result = schema.execute(
                data.get('query'),
                variables=data.get('variables'),
                context_value={"request": request, "db": db},
                operation_name=data.get('operationName')
            )
            response = {}
            if result.errors:
                response['errors'] = [str(e) for e in result.errors]
            if result.data:
                response['data'] = result.data
            return jsonify(response)
        finally:
            db.close()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
