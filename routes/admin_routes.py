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

@admin_bp.route("/bookings", methods=["GET"])
@role_required("admin")
def get_all_bookings():
    try:
        from models.booking import Booking
        from models.user import User
        from models.destination import Destination
        
        bookings = Booking.query.all()
        bookings_data = []
        
        for booking in bookings:
            traveler = User.query.get(booking.traveler_id)
            destination = Destination.query.get(booking.destination_id)
            guide = User.query.get(booking.guide_id) if booking.guide_id else None
            
            bookings_data.append({
                "id": booking.id,
                "traveler_name": traveler.full_name if traveler else "Unknown",
                "destination_name": destination.name if destination else "Unknown",
                "guide_name": guide.full_name if guide else "Not assigned",
                "date": booking.date.isoformat() if booking.date else None,
                "status": booking.status,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            })
        
        return jsonify(bookings_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@admin_bp.route("/dashboard/stats", methods=["GET"])
@role_required("admin")
def get_dashboard_stats():
    try:
        from models.user import User
        from models.destination import Destination
        from models.booking import Booking
        from models.payment import Payment
        
        total_users = User.query.count()
        total_destinations = Destination.query.count()
        total_bookings = Booking.query.count()
        active_bookings = Booking.query.filter_by(status='confirmed').count()
        
        # Calculate revenue
        total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.status == 'completed'
        ).scalar() or 0

        return jsonify({
            "totalUsers": total_users,
            "totalDestinations": total_destinations,
            "totalBookings": total_bookings,
            "activeBookings": active_bookings,
            "totalRevenue": float(total_revenue)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500