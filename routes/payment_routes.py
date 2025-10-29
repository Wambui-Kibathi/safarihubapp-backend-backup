from flask import Blueprint, jsonify, request
from utils.paystack_service import paystack_service
from utils.db import db
from models.payment import Payment
from models.booking import Booking
from utils.jwt_service import token_required

payment_bp = Blueprint("payment_bp", __name__)

@payment_bp.route("/initialize", methods=["POST"])
@token_required
def initialize_payment(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'amount', 'booking_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create payment record
        payment = Payment(
            booking_id=data['booking_id'],
            amount=data['amount'],
            method='paystack',
            status='pending',
            transaction_id=f"SH{Payment.query.count() + 1:06d}"  # Generate reference
        )
        db.session.add(payment)
        db.session.commit()
        
        # Initialize PayStack payment
        result = paystack_service.initialize_transaction(
            email=data['email'],
            amount=data['amount'],
            reference=payment.transaction_id,
            metadata={
                'booking_id': data['booking_id'],
                'user_id': current_user.id,
                'payment_id': payment.id
            }
        )
        
        if result['success']:
            payment.transaction_id = result['reference']
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "authorization_url": result['authorization_url'],
                "reference": result['reference'],
                "access_code": result['access_code']
            }), 200
        else:
            payment.status = 'failed'
            db.session.commit()
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@payment_bp.route("/verify/<reference>", methods=["GET"])
def verify_payment(reference):
    try:
        result = paystack_service.verify_transaction(reference)
        
        if result['success']:
            # Update payment status
            payment = Payment.query.filter_by(transaction_id=reference).first()
            if payment:
                payment.status = 'completed'
                
                # Update booking status
                booking = Booking.query.get(payment.booking_id)
                if booking:
                    booking.status = 'confirmed'
                
                db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Payment verified successfully",
                "data": result['data']
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": result['error']
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payment_bp.route("/webhook", methods=["POST"])
def paystack_webhook():
    """Handle PayStack webhook for real-time payment notifications"""
    try:
        # Verify webhook signature (implement based on PayStack docs)
        webhook_data = request.get_json()
        
        if webhook_data.get('event') == 'charge.success':
            reference = webhook_data['data']['reference']
            
            # Update payment status
            payment = Payment.query.filter_by(transaction_id=reference).first()
            if payment and payment.status != 'completed':
                payment.status = 'completed'
                
                # Update booking status
                booking = Booking.query.get(payment.booking_id)
                if booking:
                    booking.status = 'confirmed'
                
                db.session.commit()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500