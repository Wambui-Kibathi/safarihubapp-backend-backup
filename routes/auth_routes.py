from flask import Blueprint
from flask_restful import Api
from resources.auth_resources import UserRegistration, UserLogin, UserProfile

auth_bp = Blueprint("auth_bp", __name__)
api = Api(auth_bp)

api.add_resource(UserRegistration, "/register")
api.add_resource(UserLogin, "/login")
api.add_resource(UserProfile, "/profile")
