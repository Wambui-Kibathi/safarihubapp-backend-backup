from flask import Blueprint, request, jsonify
from utils.paystack_service import PayStackService
from models.payment import Payment
from models.booking import Booking
from utils.db import db

paystack_bp = Blueprint('paystack', __name__)
paystack_service = PayStackService()

@paystack_bp.route('/webhook/paystack', methods=['POST'])
def paystack_webhook():
    # Handle PayStack webhook for payment verification
    pass