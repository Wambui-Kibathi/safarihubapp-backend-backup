import requests
import os
from flask import current_app

class PayStackService:
    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.base_url = 'https://api.paystack.co'
    
    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initialize_transaction(self, email, amount, reference=None, metadata=None):
        """Initialize PayStack transaction"""
        url = f'{self.base_url}/transaction/initialize'
        
        payload = {
            'email': email,
            'amount': int(amount * 100),  # Convert to kobo
            'currency': 'USD',
            'callback_url': f"{os.getenv('FRONTEND_URL')}/payment/verify",
            'metadata': metadata or {}
        }
        
        if reference:
            payload['reference'] = reference
        
        try:
            response = requests.post(url, json=payload, headers=self.get_headers())
            data = response.json()
            
            if data.get('status'):
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': data['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Failed to initialize transaction')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_transaction(self, reference):
        """Verify PayStack transaction"""
        url = f'{self.base_url}/transaction/verify/{reference}'
        
        try:
            response = requests.get(url, headers=self.get_headers())
            data = response.json()
            
            if data.get('status') and data['data']['status'] == 'success':
                return {
                    'success': True,
                    'data': data['data']
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Transaction verification failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
paystack_service = PayStackService()