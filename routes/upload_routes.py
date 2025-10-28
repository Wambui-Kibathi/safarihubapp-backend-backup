# routes/upload_routes.py
from flask import Blueprint, request, jsonify
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

upload_bp = Blueprint('upload_bp', __name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Profile image upload route
@upload_bp.route("/upload/profile", methods=["POST"], strict_slashes=False)
def upload_profile_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image = request.files['image']

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image,
            folder="SafariHub/profile_pictures",  # creates a folder in your Cloudinary account
            transformation=[
                {"width": 500, "height": 500, "crop": "fill", "gravity": "face"}  # crop around face
            ]
        )

        image_url = upload_result.get("secure_url")
        return jsonify({
            "message": "Image uploaded successfully",
            "url": image_url
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
