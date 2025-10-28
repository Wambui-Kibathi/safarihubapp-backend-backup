import requests
import base64
from flask import current_app

def get_access_token():
    consumer_key = current_app.config["MPESA_CONSUMER_KEY"]
    consumer_secret = current_app.config["MPESA_CONSUMER_SECRET"]
    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(url, headers=headers)
    return response.json().get("access_token")

def process_mpesa_payment(phone, amount, account_ref):
    token = get_access_token()
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    payload = {
        "BusinessShortCode": current_app.config["MPESA_SHORTCODE"],
        "Password": "Base64EncodedPasswordHere",
        "Timestamp": "20251027120000",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": current_app.config["MPESA_SHORTCODE"],
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": account_ref,
        "TransactionDesc": "SafariHub Booking"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
