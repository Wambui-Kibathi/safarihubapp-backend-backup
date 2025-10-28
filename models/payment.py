from utils.db import db

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))  # 'stripe', 'mpesa', 'paypal'
    status = db.Column(db.String(50), default="pending")
    transaction_id = db.Column(db.String(120))
