from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api  # ← ADD THIS
from config import Config
from utils.db import db
from utils.error_handlers import register_error_handlers
from utils.cloudinary_service import configure_cloudinary
from schemas import ma

migrate = Migrate()
api = Api()  # ← INITIALIZE FLASK-RESTful

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure CORS properly for your frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "x-access-token"]
        }
    })
    
    configure_cloudinary(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    api.init_app(app)  # ← INITIALIZE API WITH APP
    ma.init_app(app) # ← INITIALIZE MARSHMALLOW WITH APP

    # Register error handlers
    register_error_handlers(app)

    # Import and register blueprints (keep for non-RESTful routes if needed)
    from routes.auth_routes import auth_bp
    from routes.contact_routes import contact_bp
    from routes.upload_routes import upload_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(contact_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")

    # Register Flask-RESTful resources
    from resources.auth_resources import UserRegistration, UserLogin, UserProfile
    from resources.traveler_resources import TravelerList, TravelerDetail
    from resources.guide_resources import GuideList, GuideDetail
    from resources.booking_resources import BookingList, BookingDetail
    from resources.destination_resources import DestinationList, DestinationDetail
    from resources.payment_resources import PaymentList, PaymentDetail, PaymentVerify
    from resources.admin_resources import AdminDashboard, AdminUsers

    # API routes with Flask-RESTful
    api.add_resource(UserRegistration, '/api/auth/register')
    api.add_resource(UserLogin, '/api/auth/login')
    api.add_resource(UserProfile, '/api/auth/profile')
    
    api.add_resource(TravelerList, '/api/travelers')
    api.add_resource(TravelerDetail, '/api/travelers/<int:traveler_id>')
    
    api.add_resource(GuideList, '/api/guides')
    api.add_resource(GuideDetail, '/api/guides/<int:guide_id>')
    
    api.add_resource(BookingList, '/api/bookings')
    api.add_resource(BookingDetail, '/api/bookings/<int:booking_id>')
    
    api.add_resource(DestinationList, '/api/destinations')
    api.add_resource(DestinationDetail, '/api/destinations/<int:destination_id>')
    
    api.add_resource(PaymentList, '/api/payments')
    api.add_resource(PaymentDetail, '/api/payments/<int:payment_id>')
    api.add_resource(PaymentVerify, '/api/payments/verify')
    
    api.add_resource(AdminDashboard, '/api/admin/dashboard')
    api.add_resource(AdminUsers, '/api/admin/users')

    @app.route('/')
    def index():
        return {"message": "SafariHub API is live!"}, 200

    return app

app = create_app()