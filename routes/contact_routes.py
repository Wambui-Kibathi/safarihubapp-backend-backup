# routes/contact_routes.py
from flask import Blueprint, request, jsonify
from models.contact import Contact
from utils.db import db
import os
from dotenv import load_dotenv

load_dotenv()

contact_bp = Blueprint('contact_bp', __name__)

# Handle contact form submissions
@contact_bp.route('/contact', methods=['POST'])
def send_message():
    try:
        data = request.get_json()

        if not all([data.get('name'), data.get('email'), data.get('message')]):
            return jsonify({"error": "All fields are required"}), 400

        new_message = Contact(
            name=data['name'],
            email=data['email'],
            message=data['message']
        )

        db.session.add(new_message)
        db.session.commit()

        return jsonify({"message": "Message received successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ✅ Generate a static Geoapify map URL
@contact_bp.route('/contact/map', methods=['GET'])
def get_static_map_url():
    api_key = os.getenv("GEOAPIFY_API_KEY")

    if not api_key:
        return jsonify({"error": "Geoapify API key not configured"}), 500

    # Nairobi coordinates
    latitude = -1.2921
    longitude = 36.8219
    zoom = 12
    width = 600
    height = 400
    marker_color = "red"

    # Static map URL using Geoapify Static Map API
    map_url = (
        f"https://maps.geoapify.com/v1/staticmap?"
        f"style=osm-bright&width={width}&height={height}"
        f"&center=lonlat:{longitude},{latitude}"
        f"&zoom={zoom}"
        f"&marker=lonlat:{longitude},{latitude};color:{marker_color};size:medium"
        f"&apiKey={api_key}"
    )

    return jsonify({
        "map_url": map_url,
        "message": "Static map URL generated successfully"
    }), 200
