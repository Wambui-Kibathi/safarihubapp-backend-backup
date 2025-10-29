from flask_restful import Resource, reqparse
from flask import request
from sqlalchemy import or_, and_
from datetime import datetime
from utils.db import db
from models.booking import Booking
from models.traveler import Traveler
from models.guide import Guide
from models.destination import Destination
from models.user import User
from schemas import BookingSchema, TravelerSchema, GuideSchema, DestinationSchema, UserSchema
from utils.jwt_service import token_required
from utils.error_handlers import ValidationError, NotFoundError, UnauthorizedError

booking_schema = BookingSchema()
traveler_schema = TravelerSchema()
guide_schema = GuideSchema()
destination_schema = DestinationSchema()
user_schema = UserSchema()

class BookingList(Resource):
    @token_required
    def get(self, user):
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status')

            # Build query based on user role
            query = Booking.query

            if user.role == 'traveler':
                # Travelers can only see their own bookings
                traveler = Traveler.query.filter_by(user_id=user.id).first()
                if not traveler:
                    return {'error': 'Traveler profile not found'}, 404
                query = query.filter(Booking.traveler_id == traveler.id)
            elif user.role == 'guide':
                # Guides can only see bookings assigned to them
                guide = Guide.query.filter_by(user_id=user.id).first()
                if not guide:
                    return {'error': 'Guide profile not found'}, 404
                query = query.filter(Booking.guide_id == guide.id)
            # Admins can see all bookings (no filter needed)

            # Apply status filter if provided
            if status_filter:
                query = query.filter(Booking.status == status_filter)

            # Order by creation date (most recent first)
            query = query.order_by(Booking.created_at.desc())

            # Paginate results
            bookings_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            bookings_data = []

            for booking in bookings_paginated.items:
                booking_data = self._serialize_booking(booking)
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

    @token_required
    def post(self, user):
        try:
            if user.role != 'traveler':
                raise UnauthorizedError('Only travelers can create bookings')

            # Get traveler profile
            traveler = Traveler.query.filter_by(user_id=user.id).first()
            if not traveler:
                return {'error': 'Traveler profile not found'}, 404

            parser = reqparse.RequestParser()
            parser.add_argument('guide_id', type=int, required=True, help='Guide ID is required')
            parser.add_argument('destination_id', type=int, required=True, help='Destination ID is required')
            parser.add_argument('date', type=str, required=True, help='Booking date is required')
            parser.add_argument('special_requests', type=str)
            args = parser.parse_args()

            # Validate guide exists and is available
            guide = Guide.query.get(args['guide_id'])
            if not guide:
                raise NotFoundError('Guide not found')

            # Validate destination exists
            destination = Destination.query.get(args['destination_id'])
            if not destination:
                raise NotFoundError('Destination not found')

            # Parse and validate date
            try:
                booking_date = datetime.fromisoformat(args['date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError('Invalid date format. Use ISO format.')

            # Check if guide is available on this date (basic check)
            existing_booking = Booking.query.filter(
                and_(
                    Booking.guide_id == guide.id,
                    Booking.date == booking_date.date(),
                    Booking.status.in_(['pending', 'confirmed'])
                )
            ).first()

            if existing_booking:
                return {'error': 'Guide is not available on this date'}, 409

            # Create booking
            new_booking = Booking(
                traveler_id=traveler.id,
                guide_id=guide.id,
                destination_id=destination.id,
                date=booking_date.date(),
                special_requests=args.get('special_requests'),
                status='pending'
            )

            db.session.add(new_booking)
            db.session.commit()

            return {
                'message': 'Booking created successfully',
                'booking': self._serialize_booking(new_booking)
            }, 201

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create booking: {str(e)}'}, 500

class BookingDetail(Resource):
    @token_required
    def get(self, user, booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                raise NotFoundError('Booking not found')

            # Check access permissions
            if not self._can_access_booking(user, booking):
                raise UnauthorizedError('Access denied')

            return {'booking': self._serialize_booking(booking)}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            return {'error': f'Failed to fetch booking: {str(e)}'}, 500

    @token_required
    def put(self, user, booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                raise NotFoundError('Booking not found')

            # Check access permissions
            if not self._can_access_booking(user, booking):
                raise UnauthorizedError('Access denied')

            parser = reqparse.RequestParser()
            parser.add_argument('status', type=str, choices=['pending', 'confirmed', 'cancelled', 'completed'])
            parser.add_argument('special_requests', type=str)
            args = parser.parse_args()

            # Update allowed fields based on role
            if user.role == 'traveler':
                # Travelers can only update special requests and cancel
                if args.get('status') and args['status'] not in ['cancelled']:
                    raise UnauthorizedError('Travelers can only cancel bookings')
                if args.get('special_requests') is not None:
                    booking.special_requests = args['special_requests']
                if args.get('status') == 'cancelled':
                    booking.status = 'cancelled'
            elif user.role in ['guide', 'admin']:
                # Guides and admins can update status
                if args.get('status'):
                    booking.status = args['status']

            db.session.commit()

            return {
                'message': 'Booking updated successfully',
                'booking': self._serialize_booking(booking)
            }, 200

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update booking: {str(e)}'}, 500

    @token_required
    def delete(self, user, booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                raise NotFoundError('Booking not found')

            # Check access permissions
            if not self._can_access_booking(user, booking):
                raise UnauthorizedError('Access denied')

            # Only allow deletion of pending bookings
            if booking.status != 'pending':
                return {'error': 'Only pending bookings can be deleted'}, 400

            # Only travelers can delete their own bookings
            if user.role != 'traveler':
                raise UnauthorizedError('Only travelers can delete bookings')

            db.session.delete(booking)
            db.session.commit()

            return {'message': 'Booking deleted successfully'}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete booking: {str(e)}'}, 500

    def _can_access_booking(self, user, booking):
        """Check if user can access this booking"""
        if user.role == 'admin':
            return True
        elif user.role == 'traveler':
            traveler = Traveler.query.filter_by(user_id=user.id).first()
            return traveler and booking.traveler_id == traveler.id
        elif user.role == 'guide':
            guide = Guide.query.filter_by(user_id=user.id).first()
            return guide and booking.guide_id == guide.id
        return False

    def _serialize_booking(self, booking):
        """Serialize booking with related data"""
        booking_data = booking_schema.dump(booking)

        # Add traveler info
        traveler = Traveler.query.get(booking.traveler_id)
        if traveler:
            traveler_user = User.query.get(traveler.user_id)
            booking_data['traveler'] = {
                'id': traveler.id,
                'user_id': traveler.user_id,
                'full_name': traveler_user.full_name if traveler_user else 'Unknown',
                'email': traveler_user.email if traveler_user else 'Unknown'
            }

        # Add guide info
        if booking.guide_id:
            guide = Guide.query.get(booking.guide_id)
            if guide:
                guide_user = User.query.get(guide.user_id)
                booking_data['guide'] = {
                    'id': guide.id,
                    'user_id': guide.user_id,
                    'full_name': guide_user.full_name if guide_user else 'Unknown',
                    'email': guide_user.email if guide_user else 'Unknown'
                }

        # Add destination info
        destination = Destination.query.get(booking.destination_id)
        if destination:
            booking_data['destination'] = destination_schema.dump(destination)

        return booking_data