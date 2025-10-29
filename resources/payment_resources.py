from flask_restful import Resource, reqparse
from flask import request
from sqlalchemy import or_, and_
from utils.db import db
from models.payment import Payment
from models.booking import Booking
from models.user import User
from models.traveler import Traveler
from schemas import PaymentSchema, BookingSchema
from utils.jwt_service import token_required
from utils.paystack_service import PayStackService  # Updated import
from utils.error_handlers import ValidationError, NotFoundError, UnauthorizedError
import uuid

payment_schema = PaymentSchema()
booking_schema = BookingSchema()
paystack_service = PayStackService()  # Initialize PayStack service

class PaymentList(Resource):
    @token_required
    def get(self, user):
        """Get payments with role-based access"""
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status')

            # Build query based on user role
            query = Payment.query

            if user.role == 'traveler':
                # Travelers can only see payments for their bookings
                traveler = Traveler.query.filter_by(user_id=user.id).first()
                if not traveler:
                    return {'error': 'Traveler profile not found'}, 404
                # Get booking IDs for this traveler
                traveler_booking_ids = db.session.query(Booking.id).filter(Booking.traveler_id == traveler.id).subquery()
                query = query.filter(Payment.booking_id.in_(traveler_booking_ids))
            elif user.role == 'guide':
                # Guides can see payments for bookings assigned to them
                from models.guide import Guide
                guide = Guide.query.filter_by(user_id=user.id).first()
                if not guide:
                    return {'error': 'Guide profile not found'}, 404
                # Get booking IDs for this guide
                guide_booking_ids = db.session.query(Booking.id).filter(Booking.guide_id == guide.id).subquery()
                query = query.filter(Payment.booking_id.in_(guide_booking_ids))
            # Admins can see all payments (no filter needed)

            # Apply status filter if provided
            if status_filter:
                query = query.filter(Payment.status == status_filter)

            # Order by creation date (most recent first)
            query = query.order_by(Payment.created_at.desc())

            # Paginate results
            payments_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            payments_data = []

            for payment in payments_paginated.items:
                payment_data = self._serialize_payment(payment)
                payments_data.append(payment_data)

            return {
                'payments': payments_data,
                'pagination': {
                    'page': payments_paginated.page,
                    'per_page': payments_paginated.per_page,
                    'total': payments_paginated.total,
                    'pages': payments_paginated.pages,
                    'has_next': payments_paginated.has_next,
                    'has_prev': payments_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch payments: {str(e)}'}, 500

    @token_required
    def post(self, user):
        """Create payment record and initiate PayStack payment"""
        try:
            if user.role != 'traveler':
                raise UnauthorizedError('Only travelers can initiate payments')

            parser = reqparse.RequestParser()
            parser.add_argument('booking_id', type=int, required=True, help='Booking ID is required')
            parser.add_argument('amount', type=float, required=True, help='Amount is required')
            parser.add_argument('callback_url', type=str, required=False, 
                              default='http://localhost:5173/payment/verify')  # Frontend verification URL
            args = parser.parse_args()

            # Validate booking exists and belongs to user
            booking = Booking.query.get(args['booking_id'])
            if not booking:
                raise NotFoundError('Booking not found')

            traveler = Traveler.query.filter_by(user_id=user.id).first()
            if not traveler:
                raise NotFoundError('Traveler profile not found')
                
            if booking.traveler_id != traveler.id:
                raise UnauthorizedError('Access denied')

            # Check if booking already has a completed payment
            existing_payment = Payment.query.filter(
                and_(Payment.booking_id == booking.id, Payment.status == 'completed')
            ).first()
            if existing_payment:
                return {'error': 'Booking already has a completed payment'}, 409

            # Generate transaction ID
            transaction_id = f"booking_{booking.id}_{uuid.uuid4().hex[:8]}"

            # Create payment record
            new_payment = Payment(
                booking_id=booking.id,
                amount=args['amount'],
                payment_method='paystack',  # Fixed field name from 'method' to 'payment_method'
                status='pending',
                transaction_id=transaction_id
            )

            db.session.add(new_payment)
            db.session.commit()

            # Initialize payment with PayStack
            payment_result = paystack_service.initialize_transaction(
                email=user.email,
                amount=args['amount'],
                reference=transaction_id,
                callback_url=args['callback_url']
            )

            if payment_result['success']:
                # Update payment with PayStack reference
                new_payment.transaction_id = payment_result['reference']  # Use PayStack reference
                db.session.commit()
                
                return {
                    'message': 'Payment initialized successfully',
                    'payment': self._serialize_payment(new_payment),
                    'authorization_url': payment_result['authorization_url'],
                    'reference': payment_result['reference'],
                    'access_code': payment_result.get('access_code', '')
                }, 201
            else:
                # Update payment status to failed
                new_payment.status = 'failed'
                db.session.commit()
                return {'error': f'Payment initialization failed: {payment_result.get("message", "Unknown error")}'}, 500

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create payment: {str(e)}'}, 500

class PaymentDetail(Resource):
    @token_required
    def get(self, user, payment_id):
        """Get specific payment details"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise NotFoundError('Payment not found')

            # Check access permissions
            if not self._can_access_payment(user, payment):
                raise UnauthorizedError('Access denied')

            return {'payment': self._serialize_payment(payment)}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            return {'error': f'Failed to fetch payment: {str(e)}'}, 500

    @token_required
    def patch(self, user, payment_id):
        """Update payment status (typically called by payment webhook or admin)"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise NotFoundError('Payment not found')

            # Check access permissions (admins can update any payment)
            if user.role != 'admin' and not self._can_access_payment(user, payment):
                raise UnauthorizedError('Access denied')

            parser = reqparse.RequestParser()
            parser.add_argument('status', type=str, required=True,
                              choices=['pending', 'processing', 'completed', 'failed', 'refunded'])
            parser.add_argument('transaction_id', type=str)
            args = parser.parse_args()

            # Update payment
            payment.status = args['status']
            if args.get('transaction_id'):
                # Validate transaction ID uniqueness
                existing_payment = Payment.query.filter(
                    and_(Payment.transaction_id == args['transaction_id'], Payment.id != payment_id)
                ).first()
                if existing_payment:
                    return {'error': 'Transaction ID already exists'}, 409
                payment.transaction_id = args['transaction_id']

            # If payment is completed, update booking status
            if args['status'] == 'completed':
                booking = Booking.query.get(payment.booking_id)
                if booking and booking.status == 'pending':
                    booking.status = 'confirmed'
                    db.session.add(booking)

            db.session.commit()

            return {
                'message': 'Payment updated successfully',
                'payment': self._serialize_payment(payment)
            }, 200

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update payment: {str(e)}'}, 500

class PaymentVerify(Resource):
    """Resource for verifying PayStack payments (webhook or manual verification)"""
    
    def post(self):
        """Verify PayStack payment (webhook endpoint)"""
        try:
            # For webhook, PayStack sends the data in the request
            if request.is_json:
                data = request.get_json()
                reference = data.get('data', {}).get('reference')
            else:
                # For manual verification
                parser = reqparse.RequestParser()
                parser.add_argument('reference', type=str, required=True, help='Reference is required')
                args = parser.parse_args()
                reference = args['reference']

            if not reference:
                return {'error': 'Reference is required'}, 400

            # Verify transaction with PayStack
            verification_result = paystack_service.verify_transaction(reference)
            
            if verification_result['success']:
                # Find payment by PayStack reference
                payment = Payment.query.filter_by(transaction_id=reference).first()
                if not payment:
                    return {'error': 'Payment not found'}, 404

                # Update payment status based on PayStack response
                paystack_status = verification_result['data']['status']
                if paystack_status == 'success':
                    payment.status = 'completed'
                    
                    # Update booking status
                    booking = Booking.query.get(payment.booking_id)
                    if booking and booking.status == 'pending':
                        booking.status = 'confirmed'
                        db.session.add(booking)
                        
                    message = 'Payment verified successfully'
                else:
                    payment.status = 'failed'
                    message = f'Payment failed: {paystack_status}'

                db.session.commit()

                return {
                    'message': message,
                    'payment': payment_schema.dump(payment),
                    'paystack_status': paystack_status
                }, 200
            else:
                return {'error': f'Payment verification failed: {verification_result.get("message", "Unknown error")}'}, 400

        except Exception as e:
            return {'error': f'Payment verification failed: {str(e)}'}, 500

    def _can_access_payment(self, user, payment):
        """Check if user can access this payment"""
        if user.role == 'admin':
            return True

        # Get the booking for this payment
        booking = Booking.query.get(payment.booking_id)
        if not booking:
            return False

        if user.role == 'traveler':
            traveler = Traveler.query.filter_by(user_id=user.id).first()
            return traveler and booking.traveler_id == traveler.id
        elif user.role == 'guide':
            from models.guide import Guide
            guide = Guide.query.filter_by(user_id=user.id).first()
            return guide and booking.guide_id == guide.id

        return False

    def _serialize_payment(self, payment):
        """Serialize payment with related booking info"""
        payment_data = payment_schema.dump(payment)

        # Add booking information
        booking = Booking.query.get(payment.booking_id)
        if booking:
            from models.destination import Destination
            from models.guide import Guide

            booking_data = {
                'id': booking.id,
                'start_date': booking.start_date.isoformat() if booking.start_date else None,
                'end_date': booking.end_date.isoformat() if booking.end_date else None,
                'status': booking.status,
                'total_price': booking.total_price
            }

            # Add destination info
            destination = Destination.query.get(booking.destination_id)
            if destination:
                booking_data['destination'] = {
                    'id': destination.id,
                    'name': destination.name,
                    'location': destination.location,
                    'price_per_day': destination.price_per_day
                }

            # Add guide info
            if booking.guide_id:
                guide = Guide.query.get(booking.guide_id)
                if guide:
                    guide_user = User.query.get(guide.user_id)
                    booking_data['guide'] = {
                        'id': guide.id,
                        'full_name': guide_user.full_name if guide_user else 'Unknown',
                        'specialties': guide.specialties
                    }

            payment_data['booking'] = booking_data

        return payment_data