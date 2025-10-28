from utils.db import db

class Destination(db.Model):
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # "popular" or "international"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "price": self.price,
            "image_url": self.image_url,
            "description": self.description,
            "category": self.category
        }