from flask import Blueprint, jsonify, request
from utils.db import db
from models.guide import Guide
from utils.jwt_service import role_required

guide_bp = Blueprint("guide_bp", __name__)

@guide_bp.route("/profile/<int:user_id>", methods=["GET"])
@role_required("guide")
def get_guide_profile(user_id):
    profile = Guide.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"error": "Guide profile not found"}), 404
    return jsonify({
        "id": profile.id,
        "experience_years": profile.experience_years,
        "languages": profile.languages,
        "bio": profile.bio
    })


@guide_bp.route("/profile", methods=["POST"])
@role_required("guide")
def create_guide_profile():
    data = request.get_json()
    guide = Guide(
        user_id=data.get("user_id"),
        experience_years=data.get("experience_years"),
        languages=data.get("languages"),
        bio=data.get("bio")
    )
    db.session.add(guide)
    db.session.commit()
    return jsonify({"message": "Guide profile created"}), 201
