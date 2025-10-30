import jwt
import datetime
from flask import current_app, request, jsonify, g
from functools import wraps
from models.user import User  # Add this import

def create_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"success": False, "message": "Token missing"}, 401

        try:
            token = auth_header.split(" ")[1]
            data = decode_token(token)
            if not data:
                return {"success": False, "message": "Invalid token"}, 401

            # Get user from database
            from models.user import User
            user = User.query.get(data.get("user_id"))
            if not user:
                return {"success": False, "message": "User not found"}, 401

            # Store user in Flask's request context for Flask-RESTful compatibility
            g.user = user
            return f(*args, **kwargs)  # Don't pass user as parameter
        except Exception as e:
            return {"success": False, "message": "Token processing failed"}, 401
    return decorated

# Keep role_required for specific role checks
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return {"success": False, "message": "Token missing"}, 401

            token = auth_header.split(" ")[1]
            data = decode_token(token)
            if not data or data.get("role") != required_role:
                return {"success": False, "message": "Unauthorized access"}, 403

            from models.user import User
            user = User.query.get(data.get("user_id"))
            if not user:
                return {"success": False, "message": "User not found"}, 401

            # Store user in Flask's request context for Flask-RESTful compatibility
            g.user = user
            return f(*args, **kwargs)  # Don't pass user as parameter
        return decorated
    return decorator