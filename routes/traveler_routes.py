from flask import Blueprint, jsonify, request
from utils.db import db
from models.traveler import Traveler
from utils.jwt_service import role_required

traveler_bp = Blueprint("traveler_bp", __name__)

@traveler_bp.route("/profile/<int:user_id>", methods=["GET"])
@role_required("traveler")
def get_traveler_profile(user_id):
    profile = Traveler.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"error": "Traveler profile not found"}), 404
    return jsonify({
        "id": profile.id,
        "nationality": profile.nationality,
        "preferences": profile.preferences
    })


@traveler_bp.route("/profile", methods=["POST"])
@role_required("traveler")
def create_traveler_profile():
    data = request.get_json()
    traveler = Traveler(
        user_id=data.get("user_id"),
        nationality=data.get("nationality"),
        preferences=data.get("preferences")
    )
    db.session.add(traveler)
    db.session.commit()
    return jsonify({"message": "Traveler profile created"}), 201
