import requests
from flask import current_app

def send_email(to, subject, message):
    api_key = current_app.config.get("SENDGRID_API_KEY")
    url = "https://api.sendgrid.com/v3/mail/send"
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": "noreply@safarihub.com"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": message}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)
