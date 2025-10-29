from flask import Blueprint, request, jsonify
from utils.db import db
from models.destination import Destination
from utils.jwt_service import role_required

destination_bp = Blueprint("destination_bp", __name__)

@destination_bp.route("/", methods=["GET"])
def get_destinations():
    try:
        category = request.args.get('category')
        if category:
            destinations = Destination.query.filter_by(category=category).all()
        else:
            destinations = Destination.query.all()
            
        return jsonify([d.to_dict() for d in destinations]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@destination_bp.route("/category/<string:category>", methods=["GET"])
def get_destinations_by_category(category):
    try:
        destinations = Destination.query.filter_by(category=category).all()
        return jsonify([d.to_dict() for d in destinations]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@destination_bp.route("/<int:destination_id>", methods=["GET"])
def get_destination(destination_id):
    try:
        destination = Destination.query.get(destination_id)
        if not destination:
            return jsonify({"error": "Destination not found"}), 404
        return jsonify(destination.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@destination_bp.route("/", methods=["POST"])
@role_required("admin")
def create_destination():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "country", "price", "category"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        destination = Destination(
            name=data["name"],
            country=data["country"],
            price=data["price"],
            image_url=data.get("image_url", ""),
            description=data.get("description", ""),
            category=data["category"]
        )
        
        db.session.add(destination)
        db.session.commit()
        
        return jsonify({
            "message": "Destination created successfully",
            "destination": destination.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@destination_bp.route("/<int:destination_id>", methods=["PUT"])
@role_required("admin")
def update_destination(destination_id):
    try:
        destination = Destination.query.get(destination_id)
        if not destination:
            return jsonify({"error": "Destination not found"}), 404
            
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            destination.name = data['name']
        if 'country' in data:
            destination.country = data['country']
        if 'price' in data:
            destination.price = data['price']
        if 'image_url' in data:
            destination.image_url = data['image_url']
        if 'description' in data:
            destination.description = data['description']
        if 'category' in data:
            destination.category = data['category']
            
        db.session.commit()
        
        return jsonify({
            "message": "Destination updated successfully",
            "destination": destination.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@destination_bp.route("/<int:destination_id>", methods=["DELETE"])
@role_required("admin")
def delete_destination(destination_id):
    try:
        destination = Destination.query.get(destination_id)
        if not destination:
            return jsonify({"error": "Destination not found"}), 404
            
        db.session.delete(destination)
        db.session.commit()
        
        return jsonify({"message": "Destination deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500