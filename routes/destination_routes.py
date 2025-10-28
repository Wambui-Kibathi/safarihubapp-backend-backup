from flask import Blueprint, request, jsonify
from utils.db import db
from models.destination import Destination
from utils.jwt_service import role_required

destination_bp = Blueprint("destination_bp", __name__)

@destination_bp.route("/", methods=["GET"])
def get_destinations():
    destinations = Destination.query.all()
    return jsonify([{
        "id": d.id,
        "name": d.name,
        "country": d.country,
        "description": d.description,
        "price": d.price,
        "image_url": d.image_url
    } for d in destinations])

@destination_bp.route("/", methods=["POST"])
@role_required("admin")
def create_destination():
    data = request.get_json()
    dest = Destination(
        name=data["name"],
        country=data["country"],
        description=data.get("description"),
        price=data.get("price"),
        image_url=data.get("image_url")
    )
    db.session.add(dest)
    db.session.commit()
    return jsonify({"message": "Destination created"}), 201
