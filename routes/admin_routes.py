from flask import Blueprint, jsonify, request
from utils.db import db
from models.admin import Admin
from models.user import User
from utils.jwt_service import role_required

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route("/assign-role", methods=["PATCH"])
@role_required("admin")
def assign_role():
    data = request.get_json()
    user = User.query.get(data.get("user_id"))
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.role = data.get("role")
    db.session.commit()
    return jsonify({"message": f"User role updated to {user.role}"}), 200
