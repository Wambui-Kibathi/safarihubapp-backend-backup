from flask import Blueprint, request, jsonify
from utils.paystack_service import paystack_service
from models.payment import Payment
from models.booking import Booking
from utils.db import db
import hmac
import hashlib
import os

paystack_bp = Blueprint('paystack', __name__)

@paystack_bp.route('/webhook/paystack', methods=['POST'])
def paystack_webhook():
    """Handle PayStack webhook for payment verification"""
    try:
        # Get the raw request data
        payload = request.get_data()
        signature = request.headers.get('X-Paystack-Signature')

        # Verify webhook signature
        secret = os.getenv('PAYSTACK_SECRET_KEY')
        if not secret:
            return jsonify({'error': 'PayStack secret not configured'}), 500

        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        # Verify signature
        if not hmac.compare_digest(expected_signature, signature or ''):
            return jsonify({'error': 'Invalid signature'}), 401

        # Parse the webhook data
        data = request.get_json()
        event = data.get('event')

        if event == 'charge.success':
            # Payment was successful
            payment_data = data.get('data', {})
            reference = payment_data.get('reference')

            if reference:
                # Find and update the payment
                payment = Payment.query.filter_by(transaction_id=reference).first()
                if payment:
                    payment.status = 'completed'

                    # Update booking status to confirmed
                    booking = Booking.query.get(payment.booking_id)
                    if booking and booking.status == 'pending':
                        booking.status = 'confirmed'

                    db.session.commit()

                    return jsonify({'status': 'success'}), 200

        elif event == 'charge.failed':
            # Payment failed
            payment_data = data.get('data', {})
            reference = payment_data.get('reference')

            if reference:
                payment = Payment.query.filter_by(transaction_id=reference).first()
                if payment:
                    payment.status = 'failed'
                    db.session.commit()

                    return jsonify({'status': 'failed payment updated'}), 200

        return jsonify({'status': 'event received'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Webhook processing failed: {str(e)}'}), 500

@paystack_bp.route('/api/payments/verify/<reference>', methods=['GET'])
def verify_payment(reference):
    """Manually verify payment status"""
    try:
        # Verify with PayStack
        result = paystack_service.verify_transaction(reference)

        if result['success']:
            # Update payment in database
            payment = Payment.query.filter_by(transaction_id=reference).first()
            if payment:
                paystack_data = result['data']
                payment.status = 'completed' if paystack_data['status'] == 'success' else 'failed'

                # Update booking if payment completed
                if payment.status == 'completed':
                    booking = Booking.query.get(payment.booking_id)
                    if booking and booking.status == 'pending':
                        booking.status = 'confirmed'

                db.session.commit()

                return jsonify({
                    'status': 'verified',
                    'payment_status': payment.status,
                    'booking_status': booking.status if booking else None
                }), 200

        return jsonify({'error': 'Verification failed', 'details': result.get('error')}), 400

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500