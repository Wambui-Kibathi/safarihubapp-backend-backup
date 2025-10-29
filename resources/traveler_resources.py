from flask_restful import Resource, reqparse
from flask import request
from sqlalchemy import or_
from utils.db import db
from models.traveler import Traveler
from models.user import User
from models.booking import Booking
from schemas import TravelerSchema, UserSchema, BookingSchema
from utils.jwt_service import token_required, role_required
from utils.error_handlers import ValidationError, NotFoundError, UnauthorizedError

traveler_schema = TravelerSchema()
user_schema = UserSchema()
booking_schema = BookingSchema()

class TravelerList(Resource):
    @role_required('admin')
    def get(self, user):
        """Get all travelers (admin only)"""
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search = request.args.get('search')

            # Build query with user join
            query = db.session.query(Traveler, User).join(User, Traveler.user_id == User.id)

            # Apply search filter
            if search:
                query = query.filter(
                    or_(
                        User.full_name.ilike(f'%{search}%'),
                        User.email.ilike(f'%{search}%'),
                        Traveler.nationality.ilike(f'%{search}%')
                    )
                )

            # Order by user name
            query = query.order_by(User.full_name)

            # Paginate results
            travelers_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            travelers_data = []

            for traveler, user in travelers_paginated.items:
                traveler_data = traveler_schema.dump(traveler)
                traveler_data.update({
                    'user_info': user_schema.dump(user),
                    'full_name': user.full_name,
                    'email': user.email,
                    'profile_image_url': user.profile_image_url
                })

                # Get booking count for this traveler
                booking_count = Booking.query.filter_by(traveler_id=traveler.id).count()
                traveler_data['total_bookings'] = booking_count

                travelers_data.append(traveler_data)

            return {
                'travelers': travelers_data,
                'pagination': {
                    'page': travelers_paginated.page,
                    'per_page': travelers_paginated.per_page,
                    'total': travelers_paginated.total,
                    'pages': travelers_paginated.pages,
                    'has_next': travelers_paginated.has_next,
                    'has_prev': travelers_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch travelers: {str(e)}'}, 500

    @token_required
    def post(self, user):
        """Create or update traveler profile (travelers only)"""
        try:
            if user.role != 'traveler':
                raise UnauthorizedError('Only travelers can create/update traveler profiles')

            # Check if traveler profile already exists
            existing_traveler = Traveler.query.filter_by(user_id=user.id).first()

            parser = reqparse.RequestParser()
            parser.add_argument('nationality', type=str)
            parser.add_argument('preferences', type=str)
            parser.add_argument('emergency_contact', type=str)
            args = parser.parse_args()

            if existing_traveler:
                # Update existing profile
                if args.get('nationality') is not None:
                    existing_traveler.nationality = args['nationality']
                if args.get('preferences') is not None:
                    existing_traveler.preferences = args['preferences']
                if args.get('emergency_contact') is not None:
                    existing_traveler.emergency_contact = args['emergency_contact']

                db.session.commit()

                return {
                    'message': 'Traveler profile updated successfully',
                    'traveler': traveler_schema.dump(existing_traveler)
                }, 200
            else:
                # Create new profile
                new_traveler = Traveler(
                    user_id=user.id,
                    nationality=args.get('nationality'),
                    preferences=args.get('preferences'),
                    emergency_contact=args.get('emergency_contact')
                )

                db.session.add(new_traveler)
                db.session.commit()

                return {
                    'message': 'Traveler profile created successfully',
                    'traveler': traveler_schema.dump(new_traveler)
                }, 201

        except ValidationError as e:
            return {'error': str(e)}, 400
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to save traveler profile: {str(e)}'}, 500

class TravelerDetail(Resource):
    @token_required
    def get(self, user, traveler_id):
        """Get specific traveler profile"""
        try:
            traveler = Traveler.query.get(traveler_id)
            if not traveler:
                raise NotFoundError('Traveler not found')

            # Check permissions
            if user.role != 'admin' and traveler.user_id != user.id:
                raise UnauthorizedError('Access denied')

            traveler_user = User.query.get(traveler.user_id)
            if not traveler_user:
                raise NotFoundError('Traveler user not found')

            traveler_data = traveler_schema.dump(traveler)
            traveler_data.update({
                'user_info': user_schema.dump(traveler_user),
                'full_name': traveler_user.full_name,
                'email': traveler_user.email,
                'profile_image_url': traveler_user.profile_image_url
            })

            # Get booking statistics
            total_bookings = Booking.query.filter_by(traveler_id=traveler.id).count()
            completed_bookings = Booking.query.filter(
                and_(Booking.traveler_id == traveler.id, Booking.status == 'completed')
            ).count()
            upcoming_bookings = Booking.query.filter(
                and_(Booking.traveler_id == traveler.id, Booking.status.in_(['pending', 'confirmed']))
            ).count()

            traveler_data.update({
                'booking_stats': {
                    'total': total_bookings,
                    'completed': completed_bookings,
                    'upcoming': upcoming_bookings
                }
            })

            return {'traveler': traveler_data}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            return {'error': f'Failed to fetch traveler: {str(e)}'}, 500

    @token_required
    def patch(self, user, traveler_id):
        """Update traveler profile (traveler owner or admin only)"""
        try:
            traveler = Traveler.query.get(traveler_id)
            if not traveler:
                raise NotFoundError('Traveler not found')

            # Check permissions
            if user.role != 'admin' and traveler.user_id != user.id:
                raise UnauthorizedError('Access denied')

            parser = reqparse.RequestParser()
            parser.add_argument('nationality', type=str)
            parser.add_argument('preferences', type=str)
            parser.add_argument('emergency_contact', type=str)
            args = parser.parse_args()

            # Update fields if provided
            if args.get('nationality') is not None:
                traveler.nationality = args['nationality']
            if args.get('preferences') is not None:
                traveler.preferences = args['preferences']
            if args.get('emergency_contact') is not None:
                traveler.emergency_contact = args['emergency_contact']

            db.session.commit()

            return {
                'message': 'Traveler profile updated successfully',
                'traveler': traveler_schema.dump(traveler)
            }, 200

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update traveler profile: {str(e)}'}, 500

class TravelerBookings(Resource):
    @token_required
    def get(self, user, traveler_id):
        """Get traveler's bookings (traveler owner or admin only)"""
        try:
            traveler = Traveler.query.get(traveler_id)
            if not traveler:
                raise NotFoundError('Traveler not found')

            # Check permissions
            if user.role != 'admin' and traveler.user_id != user.id:
                raise UnauthorizedError('Access denied')

            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status')

            # Build query
            query = Booking.query.filter(Booking.traveler_id == traveler_id)

            # Apply status filter
            if status_filter:
                query = query.filter(Booking.status == status_filter)

            # Order by date (most recent first)
            query = query.order_by(Booking.date.desc())

            # Paginate results
            bookings_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            bookings_data = []

            for booking in bookings_paginated.items:
                booking_data = self._serialize_booking_for_traveler(booking)
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

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            return {'error': f'Failed to fetch traveler bookings: {str(e)}'}, 500

    def _serialize_booking_for_traveler(self, booking):
        """Serialize booking with destination and guide info for traveler view"""
        from models.destination import Destination
        from models.guide import Guide

        booking_data = booking_schema.dump(booking)

        # Add destination info
        destination = Destination.query.get(booking.destination_id)
        if destination:
            booking_data['destination'] = {
                'id': destination.id,
                'name': destination.name,
                'country': destination.country,
                'price': destination.price,
                'image_url': destination.image_url,
                'description': destination.description
            }

        # Add guide info
        if booking.guide_id:
            guide = Guide.query.get(booking.guide_id)
            if guide:
                guide_user = User.query.get(guide.user_id)
                booking_data['guide'] = {
                    'id': guide.id,
                    'full_name': guide_user.full_name if guide_user else 'Unknown',
                    'email': guide_user.email if guide_user else 'Unknown',
                    'bio': guide.bio,
                    'languages': guide.languages,
                    'hourly_rate': guide.hourly_rate
                }

        # Add payment info
        from models.payment import Payment
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        if payment:
            booking_data['payment'] = {
                'id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'method': payment.method,
                'transaction_id': payment.transaction_id
            }

        return booking_data