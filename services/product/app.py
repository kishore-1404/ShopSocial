
from flask import Flask, request, jsonify
from schema import schema
import os
import jwt
from functools import wraps
SERVICE_JWT_SECRET = os.environ.get("SERVICE_JWT_SECRET", "changeme")

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

    @app.route('/graphql', methods=['POST'])
    @require_service_jwt
    def graphql_server():
        data = request.get_json()
        result = schema.execute(
            data.get('query'),
            variables=data.get('variables'),
            context_value=request,
            operation_name=data.get('operationName')
        )
        response = {}
        if result.errors:
            response['errors'] = [str(e) for e in result.errors]
        if result.data:
            response['data'] = result.data
        return jsonify(response)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
