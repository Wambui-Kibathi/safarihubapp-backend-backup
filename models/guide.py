from utils.db import db

class Guide(db.Model):
    __tablename__ = "guides"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    experience_years = db.Column(db.Integer)
    languages = db.Column(db.String(200))
    bio = db.Column(db.Text)
