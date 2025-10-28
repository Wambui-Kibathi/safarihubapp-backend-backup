from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config
from utils.db import db
from utils.error_handlers import register_error_handlers
from utils.cloudinary_service import configure_cloudinary

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    configure_cloudinary(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register error handlers
    register_error_handlers(app)

    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.traveler_routes import traveler_bp
    from routes.guide_routes import guide_bp
    from routes.admin_routes import admin_bp
    from routes.destination_routes import destination_bp
    from routes.booking_routes import booking_bp
    from routes.payment_routes import payment_bp
    from routes.contact_routes import contact_bp
    from routes.upload_routes import upload_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(traveler_bp, url_prefix="/traveler")
    app.register_blueprint(guide_bp, url_prefix="/guide")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(destination_bp, url_prefix="/destinations")
    app.register_blueprint(booking_bp, url_prefix="/bookings")
    app.register_blueprint(payment_bp, url_prefix="/payments")
    app.register_blueprint(contact_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")

    @app.route('/')
    def index():
        return {"message": "SafariHub API is live!"}, 200

    return app

app = create_app()
