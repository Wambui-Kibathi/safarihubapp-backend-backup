from flask import Blueprint, request, jsonify
from utils.cloudinary_service import upload_to_cloudinary
from utils.db import db
from models.user import User
from utils.jwt_service import token_required

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route("/upload/profile", methods=["POST"])
@token_required
def upload_profile_image(current_user):
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Upload to Cloudinary
        upload_result = upload_to_cloudinary(
            image_file, 
            folder="safarihub/profile_pictures"
        )

        if not upload_result["success"]:
            return jsonify({"error": upload_result["error"]}), 500

        # Update user profile in database
        current_user.profile_image_url = upload_result["url"]
        db.session.commit()

        return jsonify({
            "message": "Profile image uploaded successfully",
            "image_url": upload_result["url"]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@upload_bp.route("/upload/destination", methods=["POST"])
@token_required
def upload_destination_image(current_user):
    try:
        if current_user.role != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        upload_result = upload_to_cloudinary(
            image_file, 
            folder="safarihub/destinations"
        )

        if not upload_result["success"]:
            return jsonify({"error": upload_result["error"]}), 500

        return jsonify({
            "message": "Destination image uploaded successfully",
            "image_url": upload_result["url"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500