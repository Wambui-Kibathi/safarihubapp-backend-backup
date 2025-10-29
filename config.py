import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///safarihub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # PayStack Configuration
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")