# schemas.py - TEMPORARY DEBUG VERSION
from flask_marshmallow import Marshmallow
from utils.db import db

ma = Marshmallow()

# Import models only when needed to avoid circular imports
def create_all_schemas():
    from models.user import User
    from models.traveler import Traveler
    from models.guide import Guide
    from models.booking import Booking
    from models.destination import Destination
    from models.payment import Payment
    from models.admin import Admin

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

    return {
        'UserSchema': UserSchema,
        'TravelerSchema': TravelerSchema,
        'GuideSchema': GuideSchema,
        'DestinationSchema': DestinationSchema,
        'BookingSchema': BookingSchema,
        'PaymentSchema': PaymentSchema,
        'AdminSchema': AdminSchema
    }

# Create all schemas
schemas = create_all_schemas()
UserSchema = schemas['UserSchema']
TravelerSchema = schemas['TravelerSchema']
GuideSchema = schemas['GuideSchema']
DestinationSchema = schemas['DestinationSchema']
BookingSchema = schemas['BookingSchema']
PaymentSchema = schemas['PaymentSchema']
AdminSchema = schemas['AdminSchema']