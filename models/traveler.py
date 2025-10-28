from utils.db import db

class Traveler(db.Model):
    __tablename__ = "travelers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nationality = db.Column(db.String(100))
    preferences = db.Column(db.Text)
