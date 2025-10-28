# utils/cloudinary_service.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app

def configure_cloudinary(app=None):
    # If app provided, read from its config; otherwise rely on env vars
    if app is not None:
        cloudinary.config(
            cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
            api_key=app.config.get("CLOUDINARY_API_KEY"),
            api_secret=app.config.get("CLOUDINARY_API_SECRET"),
            secure=True
        )
    else:
        # If not provided, cloudinary reads from env vars
        cloudinary.config(secure=True)


def upload_file(file_stream, folder="safarihub", public_id=None, use_filename=True):
    """
    Upload a file-like object (werkzeug FileStorage) or file path.
    Returns the upload response dict from Cloudinary.
    """
    # Note: file_stream can be request.files['file'] (a FileStorage)
    kwargs = {
        "folder": folder,
        "use_filename": use_filename,
        "unique_filename": True,
        "overwrite": False
    }
    if public_id:
        kwargs["public_id"] = public_id
        kwargs["overwrite"] = True

    result = cloudinary.uploader.upload(file_stream, **kwargs)
    return result  # contains 'secure_url', 'public_id', etc.
