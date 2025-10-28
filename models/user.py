from utils.db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'traveler', 'guide', 'admin'

    # New field for cloudinary profile image
    profile_image_url = db.Column(db.String(255), nullable=True)

    traveler_profile = db.relationship("Traveler", backref="user", uselist=False)
    guide_profile = db.relationship("Guide", backref="user", uselist=False)
    admin_profile = db.relationship("Admin", backref="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "profile_image": self.profile_image
        }
