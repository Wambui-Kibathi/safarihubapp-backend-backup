from utils.db import db
import json

class Destination(db.Model):
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # "popular" or "international"

    # New fields for enhanced destination data
    guide_id = db.Column(db.Integer, db.ForeignKey("guides.id"), nullable=True)
    duration_days = db.Column(db.Integer, nullable=True)
    included_amenities = db.Column(db.Text, nullable=True)  # JSON array of amenities
    itinerary = db.Column(db.Text, nullable=True)
    max_travelers = db.Column(db.Integer, nullable=True)
    images = db.Column(db.Text, nullable=True)  # JSON array of image URLs

    # Relationships
    assigned_guide = db.relationship("Guide", backref="destinations", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "price": self.price,
            "image_url": self.image_url,
            "description": self.description,
            "category": self.category,
            "guide_id": self.guide_id,
            "duration_days": self.duration_days,
            "included_amenities": json.loads(self.included_amenities) if self.included_amenities else [],
            "itinerary": self.itinerary,
            "max_travelers": self.max_travelers,
            "images": json.loads(self.images) if self.images else []
        }