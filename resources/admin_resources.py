from flask_restful import Resource, reqparse
from flask import request, jsonify
from sqlalchemy import or_
from utils.db import db
from models.user import User
from models.traveler import Traveler
from models.guide import Guide
from models.booking import Booking
from models.destination import Destination
from models.payment import Payment
from schemas import UserSchema, TravelerSchema, GuideSchema, BookingSchema, DestinationSchema, PaymentSchema
from utils.jwt_service import role_required
from utils.error_handlers import ValidationError, NotFoundError

user_schema = UserSchema()
traveler_schema = TravelerSchema()
guide_schema = GuideSchema()
booking_schema = BookingSchema()
destination_schema = DestinationSchema()
payment_schema = PaymentSchema()

class AdminDashboard(Resource):
    @role_required('admin')
    def get(self, user):
        try:
            # Get statistics
            total_users = User.query.count()
            total_travelers = Traveler.query.count()
            total_guides = Guide.query.count()
            total_destinations = Destination.query.count()
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter_by(status='confirmed').count()

            # Calculate total revenue from completed payments
            total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.status == 'completed'
            ).scalar() or 0

            # Get recent bookings (last 10)
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
            recent_bookings_data = []
            for booking in recent_bookings:
                traveler = Traveler.query.get(booking.traveler_id)
                traveler_user = User.query.get(traveler.user_id) if traveler else None
                destination = Destination.query.get(booking.destination_id)
                guide = Guide.query.get(booking.guide_id)
                guide_user = User.query.get(guide.user_id) if guide else None

                recent_bookings_data.append({
                    'id': booking.id,
                    'traveler_name': traveler_user.full_name if traveler_user else 'Unknown',
                    'destination_name': destination.name if destination else 'Unknown',
                    'guide_name': guide_user.full_name if guide_user else 'Not assigned',
                    'status': booking.status,
                    'created_at': booking.created_at.isoformat() if booking.created_at else None
                })

            return {
                'statistics': {
                    'total_users': total_users,
                    'total_travelers': total_travelers,
                    'total_guides': total_guides,
                    'total_destinations': total_destinations,
                    'total_bookings': total_bookings,
                    'active_bookings': active_bookings,
                    'total_revenue': float(total_revenue)
                },
                'recent_bookings': recent_bookings_data
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch dashboard data: {str(e)}'}, 500

class AdminUsers(Resource):
    @role_required('admin')
    def get(self, user):
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search = request.args.get('search', '')

            # Build query
            query = User.query

            # Apply search filter
            if search:
                query = query.filter(
                    or_(
                        User.full_name.ilike(f'%{search}%'),
                        User.email.ilike(f'%{search}%')
                    )
                )

            # Paginate results
            users_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            users_data = []

            for user in users_paginated.items:
                user_data = user_schema.dump(user)

                # Add role-specific profile data
                if user.role == 'traveler':
                    traveler = Traveler.query.filter_by(user_id=user.id).first()
                    if traveler:
                        user_data['traveler_profile'] = traveler_schema.dump(traveler)
                elif user.role == 'guide':
                    guide = Guide.query.filter_by(user_id=user.id).first()
                    if guide:
                        user_data['guide_profile'] = guide_schema.dump(guide)

                users_data.append(user_data)

            return {
                'users': users_data,
                'pagination': {
                    'page': users_paginated.page,
                    'per_page': users_paginated.per_page,
                    'total': users_paginated.total,
                    'pages': users_paginated.pages,
                    'has_next': users_paginated.has_next,
                    'has_prev': users_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch users: {str(e)}'}, 500

class AdminUserUpdate(Resource):
    @role_required('admin')
    def put(self, user, user_id):
        try:
            target_user = User.query.get(user_id)
            if not target_user:
                raise NotFoundError('User not found')

            parser = reqparse.RequestParser()
            parser.add_argument('role', type=str, choices=['traveler', 'guide', 'admin'])
            parser.add_argument('is_active', type=bool)
            args = parser.parse_args()

            # Update user fields
            if args.get('role'):
                target_user.role = args['role']
            if args.get('is_active') is not None:
                # Assuming we add an is_active field to User model
                if hasattr(target_user, 'is_active'):
                    target_user.is_active = args['is_active']

            db.session.commit()

            return {
                'message': 'User updated successfully',
                'user': user_schema.dump(target_user)
            }, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except ValidationError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update user: {str(e)}'}, 500

class AdminBookings(Resource):
    @role_required('admin')
    def get(self, user):
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status')

            # Build query
            query = Booking.query

            # Apply status filter
            if status_filter:
                query = query.filter(Booking.status == status_filter)

            # Order by creation date
            query = query.order_by(Booking.created_at.desc())

            # Paginate results
            bookings_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            bookings_data = []

            for booking in bookings_paginated.items:
                traveler = Traveler.query.get(booking.traveler_id)
                traveler_user = User.query.get(traveler.user_id) if traveler else None
                destination = Destination.query.get(booking.destination_id)
                guide = Guide.query.get(booking.guide_id)
                guide_user = User.query.get(guide.user_id) if guide else None

                # Get payment info
                payment = Payment.query.filter_by(booking_id=booking.id).first()

                booking_data = booking_schema.dump(booking)
                booking_data.update({
                    'traveler_name': traveler_user.full_name if traveler_user else 'Unknown',
                    'traveler_email': traveler_user.email if traveler_user else 'Unknown',
                    'destination_name': destination.name if destination else 'Unknown',
                    'guide_name': guide_user.full_name if guide_user else 'Not assigned',
                    'guide_email': guide_user.email if guide_user else None,
                    'payment_status': payment.status if payment else 'No payment',
                    'payment_amount': payment.amount if payment else 0
                })

                bookings_data.append(booking_data)

            return {
                'bookings': bookings_data,
                'pagination': {
                    'page': bookings_paginated.page,
                    'per_page': bookings_paginated.per_page,
                    'total': bookings_paginated.total,
                    'pages': bookings_paginated.pages,
                    'has_next': bookings_paginated.has_next,
                    'has_prev': bookings_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch bookings: {str(e)}'}, 500

class AdminGuides(Resource):
    @role_required('admin')
    def get(self, user):
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            approval_status = request.args.get('approval_status')  # 'pending', 'approved', 'rejected'

            # Get guides with their user info
            guides_query = db.session.query(Guide, User).join(User, Guide.user_id == User.id)

            # Apply approval status filter (assuming we add approval_status to Guide model)
            if approval_status:
                if hasattr(Guide, 'approval_status'):
                    guides_query = guides_query.filter(Guide.approval_status == approval_status)

            # Order by creation date
            guides_query = guides_query.order_by(Guide.created_at.desc())

            # Paginate results
            guides_paginated = guides_query.paginate(page=page, per_page=per_page, error_out=False)
            guides_data = []

            for guide, user in guides_paginated.items:
                guide_data = guide_schema.dump(guide)
                guide_data.update({
                    'user_info': user_schema.dump(user),
                    'full_name': user.full_name,
                    'email': user.email,
                    'profile_image_url': user.profile_image_url,
                    'approval_status': getattr(guide, 'approval_status', 'pending')  # Default to pending if not set
                })

                # Get booking count for this guide
                booking_count = Booking.query.filter_by(guide_id=guide.id).count()
                guide_data['total_bookings'] = booking_count

                guides_data.append(guide_data)

            return {
                'guides': guides_data,
                'pagination': {
                    'page': guides_paginated.page,
                    'per_page': guides_paginated.per_page,
                    'total': guides_paginated.total,
                    'pages': guides_paginated.pages,
                    'has_next': guides_paginated.has_next,
                    'has_prev': guides_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch guides: {str(e)}'}, 500