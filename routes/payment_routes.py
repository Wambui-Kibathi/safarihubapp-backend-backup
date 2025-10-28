from flask import Blueprint, jsonify, request
from utils.stripe_service import process_stripe_payment
from utils.mpesa_service import process_mpesa_payment

payment_bp = Blueprint("payment_bp", __name__)

@payment_bp.route("/stripe", methods=["POST"])
def stripe_payment():
    data = request.get_json()
    result = process_stripe_payment(data["amount"], data["token"])
    return jsonify(result), 200


@payment_bp.route("/mpesa", methods=["POST"])
def mpesa_payment():
    data = request.get_json()
    result = process_mpesa_payment(
        phone=data["phone"],
        amount=data["amount"],
        account_ref=data.get("account_ref", "SafariHub")
    )
    return jsonify(result), 200
