from utils.db import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default="paystack")  # CHANGED: field name and default value
    status = db.Column(db.String(50), default="pending")  # pending, processing, completed, failed, refunded
    transaction_id = db.Column(db.String(120), unique=True)  # PayStack reference
    paystack_access_code = db.Column(db.String(100))  # NEW: PayStack access code
    currency = db.Column(db.String(10), default="KES")  # NEW: Currency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with Booking
    booking = db.relationship("Booking", backref="payments", lazy=True)

    def __init__(self, booking_id, amount, payment_method="paystack", status="pending", transaction_id=None, paystack_access_code=None):
        self.booking_id = booking_id
        self.amount = amount
        self.payment_method = payment_method
        self.status = status
        self.transaction_id = transaction_id
        self.paystack_access_code = paystack_access_code

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'paystack_access_code': self.paystack_access_code,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Payment {self.id} - {self.status} - {self.amount}>'