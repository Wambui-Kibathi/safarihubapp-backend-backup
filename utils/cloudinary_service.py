import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os

def configure_cloudinary(app):
    """Configure Cloudinary with the app context"""
    cloudinary.config(
        cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME") or os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=app.config.get("CLOUDINARY_API_KEY") or os.getenv("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET") or os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

def upload_to_cloudinary(file, folder="safarihub"):
    """Upload file to Cloudinary and return URL"""
    try:
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            use_filename=True,
            unique_filename=True,
            overwrite=False
        )
        return {
            "success": True,
            "url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }