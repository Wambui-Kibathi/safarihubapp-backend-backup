from flask_restful import Resource, reqparse
from flask import request
from sqlalchemy import or_, and_
from utils.db import db
from models.destination import Destination
from schemas import DestinationSchema
from utils.jwt_service import token_required, role_required
from utils.error_handlers import ValidationError, NotFoundError, UnauthorizedError

destination_schema = DestinationSchema()

class DestinationList(Resource):
    def get(self):
        """Get all destinations (public access)"""
        try:
            # Pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # Filtering parameters
            location_filter = request.args.get('location')  # Filter by country
            category_filter = request.args.get('category')  # Filter by category
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            search = request.args.get('search')  # Search in name or description

            # Build query
            query = Destination.query

            # Apply filters
            if location_filter:
                query = query.filter(Destination.country.ilike(f'%{location_filter}%'))

            if category_filter:
                query = query.filter(Destination.category == category_filter)

            if min_price is not None:
                query = query.filter(Destination.price >= min_price)

            if max_price is not None:
                query = query.filter(Destination.price <= max_price)

            if search:
                query = query.filter(
                    or_(
                        Destination.name.ilike(f'%{search}%'),
                        Destination.description.ilike(f'%{search}%'),
                        Destination.country.ilike(f'%{search}%')
                    )
                )

            # Order by name
            query = query.order_by(Destination.name)

            # Paginate results
            destinations_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            destinations_data = [destination_schema.dump(dest) for dest in destinations_paginated.items]

            return {
                'destinations': destinations_data,
                'pagination': {
                    'page': destinations_paginated.page,
                    'per_page': destinations_paginated.per_page,
                    'total': destinations_paginated.total,
                    'pages': destinations_paginated.pages,
                    'has_next': destinations_paginated.has_next,
                    'has_prev': destinations_paginated.has_prev
                }
            }, 200

        except Exception as e:
            return {'error': f'Failed to fetch destinations: {str(e)}'}, 500

    @role_required('admin')
    def post(self, user):
        """Create new destination (admin only)"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str, required=True, help='Name is required')
            parser.add_argument('country', type=str, required=True, help='Country is required')
            parser.add_argument('price', type=float, required=True, help='Price is required')
            parser.add_argument('image_url', type=str, required=True, help='Image URL is required')
            parser.add_argument('description', type=str)
            parser.add_argument('category', type=str, required=True, help='Category is required',
                              choices=['popular', 'international'])
            parser.add_argument('guide_id', type=int)
            parser.add_argument('duration_days', type=int)
            parser.add_argument('included_amenities', type=str)  # JSON string
            parser.add_argument('itinerary', type=str)
            parser.add_argument('max_travelers', type=int)
            parser.add_argument('images', type=str)  # JSON string
            args = parser.parse_args()

            # Check if destination with same name already exists
            existing_destination = Destination.query.filter_by(name=args['name']).first()
            if existing_destination:
                return {'error': 'Destination with this name already exists'}, 409

            # Create new destination
            new_destination = Destination(
                name=args['name'],
                country=args['country'],
                price=args['price'],
                image_url=args['image_url'],
                description=args.get('description'),
                category=args['category'],
                guide_id=args.get('guide_id'),
                duration_days=args.get('duration_days'),
                included_amenities=args.get('included_amenities'),
                itinerary=args.get('itinerary'),
                max_travelers=args.get('max_travelers'),
                images=args.get('images')
            )

            db.session.add(new_destination)
            db.session.commit()

            return {
                'message': 'Destination created successfully',
                'destination': destination_schema.dump(new_destination)
            }, 201

        except ValidationError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create destination: {str(e)}'}, 500

class DestinationDetail(Resource):
    def get(self, destination_id):
        """Get specific destination with comprehensive data (public access)"""
        try:
            destination = Destination.query.get(destination_id)
            if not destination:
                raise NotFoundError('Destination not found')

            # Get comprehensive destination data
            destination_data = destination_schema.dump(destination)

            # Add assigned guide information if exists
            if destination.assigned_guide:
                guide_user = destination.assigned_guide.user
                destination_data['assigned_guide'] = {
                    'id': destination.assigned_guide.id,
                    'full_name': guide_user.full_name if guide_user else 'Unknown',
                    'email': guide_user.email if guide_user else 'Unknown',
                    'bio': destination.assigned_guide.bio,
                    'languages': destination.assigned_guide.languages,
                    'experience_years': destination.assigned_guide.experience_years,
                    'hourly_rate': destination.assigned_guide.hourly_rate
                }

            # Parse JSON fields
            import json
            if destination.included_amenities:
                try:
                    destination_data['included_amenities'] = json.loads(destination.included_amenities)
                except:
                    destination_data['included_amenities'] = []

            if destination.images:
                try:
                    destination_data['images'] = json.loads(destination.images)
                except:
                    destination_data['images'] = []

            return {'destination': destination_data}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': f'Failed to fetch destination: {str(e)}'}, 500

    @role_required('admin')
    def patch(self, user, destination_id):
        """Update destination (admin only)"""
        try:
            destination = Destination.query.get(destination_id)
            if not destination:
                raise NotFoundError('Destination not found')

            parser = reqparse.RequestParser()
            parser.add_argument('name', type=str)
            parser.add_argument('country', type=str)
            parser.add_argument('price', type=float)
            parser.add_argument('image_url', type=str)
            parser.add_argument('description', type=str)
            parser.add_argument('category', type=str, choices=['popular', 'international'])
            parser.add_argument('guide_id', type=int)
            parser.add_argument('duration_days', type=int)
            parser.add_argument('included_amenities', type=str)  # JSON string
            parser.add_argument('itinerary', type=str)
            parser.add_argument('max_travelers', type=int)
            parser.add_argument('images', type=str)  # JSON string
            args = parser.parse_args()

            # Update fields if provided
            if args.get('name'):
                # Check if new name conflicts with existing destination
                existing_destination = Destination.query.filter(
                    and_(Destination.name == args['name'], Destination.id != destination_id)
                ).first()
                if existing_destination:
                    return {'error': 'Destination with this name already exists'}, 409
                destination.name = args['name']

            if args.get('country'):
                destination.country = args['country']
            if args.get('price') is not None:
                destination.price = args['price']
            if args.get('image_url'):
                destination.image_url = args['image_url']
            if args.get('description') is not None:
                destination.description = args['description']
            if args.get('category'):
                destination.category = args['category']
            if args.get('guide_id') is not None:
                destination.guide_id = args['guide_id']
            if args.get('duration_days') is not None:
                destination.duration_days = args['duration_days']
            if args.get('included_amenities') is not None:
                destination.included_amenities = args['included_amenities']
            if args.get('itinerary') is not None:
                destination.itinerary = args['itinerary']
            if args.get('max_travelers') is not None:
                destination.max_travelers = args['max_travelers']
            if args.get('images') is not None:
                destination.images = args['images']

            db.session.commit()

            return {
                'message': 'Destination updated successfully',
                'destination': destination_schema.dump(destination)
            }, 200

        except ValidationError as e:
            return {'error': str(e)}, 400
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update destination: {str(e)}'}, 500

    @role_required('admin')
    def delete(self, user, destination_id):
        """Delete destination (admin only)"""
        try:
            destination = Destination.query.get(destination_id)
            if not destination:
                raise NotFoundError('Destination not found')

            # Check if destination is referenced in any bookings
            from models.booking import Booking
            active_bookings = Booking.query.filter(
                and_(
                    Booking.destination_id == destination_id,
                    Booking.status.in_(['pending', 'confirmed'])
                )
            ).count()

            if active_bookings > 0:
                return {'error': 'Cannot delete destination with active bookings'}, 409

            db.session.delete(destination)
            db.session.commit()

            return {'message': 'Destination deleted successfully'}, 200

        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete destination: {str(e)}'}, 500