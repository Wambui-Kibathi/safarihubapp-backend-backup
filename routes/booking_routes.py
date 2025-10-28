from flask import Blueprint, jsonify, request
from utils.db import db
from models.booking import Booking
from utils.jwt_service import role_required

booking_bp = Blueprint("booking_bp", __name__)

@booking_bp.route("/", methods=["POST"])
@role_required("traveler")
def create_booking():
    data = request.get_json()
    booking = Booking(
        traveler_id=data["traveler_id"],
        guide_id=data.get("guide_id"),
        destination_id=data["destination_id"],
        date=data.get("date"),
        status="pending"
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking created"}), 201


@booking_bp.route("/<int:booking_id>/status", methods=["PATCH"])
@role_required("guide")
def update_status(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    booking.status = request.get_json().get("status", "confirmed")
    db.session.commit()
    return jsonify({"message": f"Booking {booking.status}"}), 200
