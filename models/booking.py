from utils.db import db

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    traveler_id = db.Column(db.Integer, db.ForeignKey("travelers.id"), nullable=False)
    guide_id = db.Column(db.Integer, db.ForeignKey("guides.id"))
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"))
    date = db.Column(db.Date)
    status = db.Column(db.String(50), default="pending")
