# schemas.py
from flask_marshmallow import Marshmallow
from models.user import User
from models.traveler import Traveler
from models.guide import Guide
from models.booking import Booking
from models.destination import Destination
from models.payment import Payment
from models.admin import Admin
from utils.db import db

ma = Marshmallow()

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True

class TravelerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Traveler
        load_instance = True
        include_fk = True

class GuideSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Guide
        load_instance = True
        include_fk = True

class DestinationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Destination
        load_instance = True
        include_fk = True

class BookingSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Booking
        load_instance = True
        include_fk = True

class PaymentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True
        include_fk = True

class AdminSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Admin
        load_instance = True
        include_fk = True