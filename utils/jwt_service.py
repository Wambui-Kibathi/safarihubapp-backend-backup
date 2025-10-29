import jwt
import datetime
from flask import current_app, request, jsonify
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

def token_required(f):  # RENAME THIS from role_required
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token missing"}), 401
        
        try:
            token = auth_header.split(" ")[1]
            data = decode_token(token)
            if not data:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Get user from database to ensure they still exist
            user = User.query.get(data.get("user_id"))
            if not user:
                return jsonify({"error": "User not found"}), 401
            
            return f(user, *args, **kwargs)  # Pass user object to route
        except Exception as e:
            return jsonify({"error": "Token processing failed"}), 401
    
    return decorated

# Keep role_required for specific role checks
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # This will use token_required first, then check role
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "Token missing"}), 401
            
            token = auth_header.split(" ")[1]
            data = decode_token(token)
            if not data or data.get("role") != required_role:
                return jsonify({"error": "Unauthorized access"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator