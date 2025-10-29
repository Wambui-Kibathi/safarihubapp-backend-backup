from flask_restful import Resource, reqparse
from flask import request
from sqlalchemy import or_, and_
from utils.db import db
from models.guide import Guide
from models.user import User
from models.booking import Booking
from schemas import GuideSchema, UserSchema, BookingSchema
from utils.jwt_service import token_required, role_required
from utils.error_handlers import ValidationError, NotFoundError, UnauthorizedError

guide_schema = GuideSchema()
user_schema = UserSchema()
booking_schema = BookingSchema()

class GuideList(Resource):
    def get(self):
        """Get all guides (public access with filtering)"""
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # Filtering parameters
            available_only = request.args.get('available', type=bool)
            languages = request.args.get('languages')  # Comma-separated languages
            search = request.args.get('search')  # Search in bio or user name

            # Build query with user join
            query = db.session.query(Guide, User).join(User, Guide.user_id == User.id)

            # Apply filters
            if available_only:
                query = query.filter(Guide.is_available == True)

            if languages:
                language_list = [lang.strip() for lang in languages.split(',')]
                for lang in language_list:
                    query = query.filter(Guide.languages.ilike(f'%{lang}%'))

            if search:
                query = query.filter(
                    or_(
                        Guide.bio.ilike(f'%{search}%'),
                        User.full_name.ilike(f'%{search}%')
                    )
                )

            # Order by user name
            query = query.order_by(User.full_name)

            # Paginate results
            guides_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            guides_data = []

            for guide, user in guides_paginated.items:
                guide_data = guide_schema.dump(guide)
                guide_data.update({
                    'user_info': {
                        'id': user.id,
                        'full_name': user.full_name,
                        'email': user.email,
                        'profile_image_url': user.profile_image_url
                    }
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

    @token_required
    def post(self, user):
        """Create or update guide profile (guides only)"""
        try:
            if user.role != 'guide':
                raise UnauthorizedError('Only guides can create/update guide profiles')

            # Check if guide profile already exists
            existing_guide = Guide.query.filter_by(user_id=user.id).first()

            parser = reqparse.RequestParser()
            parser.add_argument('experience_years', type=int)
            parser.add_argument('languages', type=str)
            parser.add_argument('bio', type=str)
            parser.add_argument('specialties', type=str)
            parser.add_argument('hourly_rate', type=float)
            parser.add_argument('is_available', type=bool)
            parser.add_argument('license_number', type=str)
            args = parser.parse_args()

            if existing_guide:
                # Update existing profile
                if args.get('experience_years') is not None:
                    existing_guide.experience_years = args['experience_years']
                if args.get('languages'):
                    existing_guide.languages = args['languages']
                if args.get('bio') is not None:
                    existing_guide.bio = args['bio']
                if args.get('specialties'):
                    existing_guide.specialties = args['specialties']
                if args.get('hourly_rate') is not None:
                    existing_guide.hourly_rate = args['hourly_rate']
                if args.get('is_available') is not None:
                    existing_guide.is_available = args['is_available']
                if args.get('license_number'):
                    existing_guide.license_number = args['license_number']

                db.session.commit()

                return {
                    'message': 'Guide profile updated successfully',
                    'guide': guide_schema.dump(existing_guide)
                }, 200
            else:
                # Create new profile
                new_guide = Guide(
                    user_id=user.id,
                    experience_years=args.get('experience_years'),
                    languages=args.get('languages'),
                    bio=args.get('bio'),
                    specialties=args.get('specialties'),
                    hourly_rate=args.get('hourly_rate'),
                    is_available=args.get('is_available', True),
                    license_number=args.get('license_number')
                )

                db.session.add(new_guide)
                db.session.commit()

                return {
                    'message': 'Guide profile created successfully',
                    'guide': guide_schema.dump(new_guide)
                }, 201

        except ValidationError as e:
            return {'error': str(e)}, 400
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to save guide profile: {str(e)}'}, 500

class GuideDetail(Resource):
    def get(self, guide_id):
        """Get specific guide profile (public access)"""
        try:
            guide = Guide.query.get(guide_id)
            if not guide:
                raise NotFoundError('Guide not found')

            user = User.query.get(guide.user_id)
            if not user:
                raise NotFoundError('Guide user not found')

            guide_data = guide_schema.dump(guide)
            guide_data.update({
                'user_info': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'email': user.email,
                    'profile_image_url': user.profile_image_url
                }
            })

            # Get booking statistics
            total_bookings = Booking.query.filter_by(guide_id=guide.id).count()
            completed_bookings = Booking.query.filter(
                and_(Booking.guide_id == guide.id, Booking.status == 'completed')
            ).count()

            guide_data.update({
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings
            })

            return {'guide': guide_data}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': f'Failed to fetch guide: {str(e)}'}, 500

    @token_required
    def put(self, user, guide_id):
        """Update guide profile (guide owner or admin only)"""
        try:
            guide = Guide.query.get(guide_id)
            if not guide:
                raise NotFoundError('Guide not found')

            # Check permissions
            if user.role != 'admin' and guide.user_id != user.id:
                raise UnauthorizedError('Access denied')

            parser = reqparse.RequestParser()
            parser.add_argument('experience_years', type=int)
            parser.add_argument('languages', type=str)
            parser.add_argument('bio', type=str)
            parser.add_argument('specialties', type=str)
            parser.add_argument('hourly_rate', type=float)
            parser.add_argument('is_available', type=bool)
            parser.add_argument('license_number', type=str)
            args = parser.parse_args()

            # Update fields if provided
            if args.get('experience_years') is not None:
                guide.experience_years = args['experience_years']
            if args.get('languages'):
                guide.languages = args['languages']
            if args.get('bio') is not None:
                guide.bio = args['bio']
            if args.get('specialties'):
                guide.specialties = args['specialties']
            if args.get('hourly_rate') is not None:
                guide.hourly_rate = args['hourly_rate']
            if args.get('is_available') is not None:
                guide.is_available = args['is_available']
            if args.get('license_number'):
                guide.license_number = args['license_number']

            db.session.commit()

            return {
                'message': 'Guide profile updated successfully',
                'guide': guide_schema.dump(guide)
            }, 200

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except UnauthorizedError as e:
            return {'error': str(e)}, 403
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update guide profile: {str(e)}'}, 500

class GuideBookings(Resource):
    @token_required
    def get(self, user, guide_id):
        """Get guide's bookings (guide owner or admin only)"""
        try:
            guide = Guide.query.get(guide_id)
            if not guide:
                raise NotFoundError('Guide not found')

            # Check permissions
            if user.role != 'admin' and guide.user_id != user.id:
                raise UnauthorizedError('Access denied')

            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status')

            # Build query
            query = Booking.query.filter(Booking.guide_id == guide_id)

            # Apply status filter
            if status_filter:
                query = query.filter(Booking.status == status_filter)

            # Order by date (most recent first)
            query = query.order_by(Booking.date.desc())

            # Paginate results
            bookings_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            bookings_data = []

            for booking in bookings_paginated.items:
                booking_data = self._serialize_booking_for_guide(booking)
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
            return {'error': f'Failed to fetch guide bookings: {str(e)}'}, 500

    def _serialize_booking_for_guide(self, booking):
        """Serialize booking with traveler and destination info for guide view"""
        from models.traveler import Traveler
        from models.destination import Destination

        booking_data = booking_schema.dump(booking)

        # Add traveler info
        traveler = Traveler.query.get(booking.traveler_id)
        if traveler:
            traveler_user = User.query.get(traveler.user_id)
            booking_data['traveler'] = {
                'id': traveler.id,
                'full_name': traveler_user.full_name if traveler_user else 'Unknown',
                'email': traveler_user.email if traveler_user else 'Unknown',
                'nationality': traveler.nationality
            }

        # Add destination info
        destination = Destination.query.get(booking.destination_id)
        if destination:
            booking_data['destination'] = {
                'id': destination.id,
                'name': destination.name,
                'country': destination.country,
                'price': destination.price
            }

        return booking_data