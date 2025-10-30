from flask_restful import Resource, reqparse
from flask import request, g
from models.user import User
from models.traveler import Traveler
from models.guide import Guide
from utils.db import db
from utils.jwt_service import create_token, token_required
from schemas import UserSchema, TravelerSchema, GuideSchema

user_schema = UserSchema()
traveler_schema = TravelerSchema()
guide_schema = GuideSchema()

class UserRegistration(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('full_name', type=str, required=True, help='Full name is required')
            parser.add_argument('email', type=str, required=True, help='Email is required')
            parser.add_argument('password', type=str, required=True, help='Password is required')
            parser.add_argument('role', type=str, required=True, help='Role is required')
            args = parser.parse_args()

            # Check if user already exists
            existing_user = User.query.filter_by(email=args['email']).first()
            if existing_user:
                return {'success': False, 'message': 'User with this email already exists'}, 400

            # Create new user
            new_user = User(
                full_name=args['full_name'],
                email=args['email'],
                role=args['role'].lower()
            )
            new_user.set_password(args['password'])

            db.session.add(new_user)
            db.session.commit()

            # Create role-specific profile
            if args['role'].lower() == 'traveler':
                traveler = Traveler(user_id=new_user.id)
                db.session.add(traveler)
            elif args['role'].lower() == 'guide':
                guide = Guide(user_id=new_user.id)
                db.session.add(guide)

            db.session.commit()

            # Generate token
            token = create_token(new_user.id, new_user.role)

            return {
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': new_user.id,
                    'full_name': new_user.full_name,
                    'email': new_user.email,
                    'role': new_user.role
                },
                'token': token
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Registration failed: {str(e)}'}, 500

class UserLogin(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('email', type=str, required=True, help='Email is required')
            parser.add_argument('password', type=str, required=True, help='Password is required')
            args = parser.parse_args()

            user = User.query.filter_by(email=args['email']).first()

            if not user or not user.check_password(args['password']):
                return {'success': False, 'message': 'Invalid email or password'}, 401

            # Generate token
            token = create_token(user.id, user.role)

            # Get role-specific data
            user_data = user_schema.dump(user)
            if user.role == 'traveler':
                traveler = Traveler.query.filter_by(user_id=user.id).first()
                if traveler:
                    user_data['traveler_profile'] = traveler_schema.dump(traveler)
            elif user.role == 'guide':
                guide = Guide.query.filter_by(user_id=user.id).first()
                if guide:
                    user_data['guide_profile'] = guide_schema.dump(guide)

            return {
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role
                },
                'token': token
            }, 200

        except Exception as e:
            return {'success': False, 'message': f'Login failed: {str(e)}'}, 500

class UserProfile(Resource):
    @token_required
    def get(self):
        try:
            user = g.user  # Retrieve user from Flask context

            # Add role-specific data
            user_data = {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'profile_image_url': user.profile_image_url
            }

            if user.role == 'traveler':
                traveler = Traveler.query.filter_by(user_id=user.id).first()
                if traveler:
                    user_data['traveler_profile'] = traveler_schema.dump(traveler)
            elif user.role == 'guide':
                guide = Guide.query.filter_by(user_id=user.id).first()
                if guide:
                    user_data['guide_profile'] = guide_schema.dump(guide)

            return {
                'success': True,
                'user': user_data
            }, 200

        except Exception as e:
            return {'success': False, 'message': f'Failed to fetch profile: {str(e)}'}, 500