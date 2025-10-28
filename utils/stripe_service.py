import stripe
from flask import current_app

def process_stripe_payment(amount, token):
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),
            currency="usd",
            description="SafariHub Payment",
            source=token
        )
        return {"status": "success", "transaction_id": charge.id}
    except stripe.error.StripeError as e:
        return {"status": "error", "message": str(e)}
