import requests
import os
from flask import current_app

class PayStackService:
    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.public_key = os.getenv('PAYSTACK_PUBLIC_KEY')
        self.base_url = 'https://api.paystack.co'

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def initialize_transaction(self, email, amount, reference=None, callback_url=None):
        """Initialize a PayStack transaction"""
        try:
            url = f"{self.base_url}/transaction/initialize"
            payload = {
                'email': email,
                'amount': int(amount * 100),  # PayStack expects amount in kobo
                'reference': reference,
                'callback_url': callback_url
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            response_data = response.json()
            
            if response_data.get('status'):
                return {
                    'success': True,
                    'authorization_url': response_data['data']['authorization_url'],
                    'access_code': response_data['data']['access_code'],
                    'reference': response_data['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Failed to initialize transaction')
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error initializing transaction: {str(e)}'
            }

    def verify_transaction(self, reference):
        """Verify a PayStack transaction"""
        try:
            url = f"{self.base_url}/transaction/verify/{reference}"
            response = requests.get(url, headers=self.get_headers())
            response_data = response.json()
            
            if response_data.get('status') and response_data['data']['status'] == 'success':
                return {
                    'success': True,
                    'data': response_data['data'],
                    'message': 'Transaction verified successfully'
                }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Transaction verification failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error verifying transaction: {str(e)}'
            }

    def create_transfer_recipient(self, name, account_number, bank_code, type='nuban'):
        """Create a transfer recipient for guide payouts"""
        try:
            url = f"{self.base_url}/transferrecipient"
            payload = {
                'type': type,
                'name': name,
                'account_number': account_number,
                'bank_code': bank_code,
                'currency': 'KES'
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            response_data = response.json()
            
            if response_data.get('status'):
                return {
                    'success': True,
                    'recipient_code': response_data['data']['recipient_code']
                }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Failed to create transfer recipient')
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating transfer recipient: {str(e)}'
            }

    def initiate_transfer(self, recipient_code, amount, reason):
        """Initiate transfer to guide (payout)"""
        try:
            url = f"{self.base_url}/transfer"
            payload = {
                'source': 'balance',
                'amount': int(amount * 100),  # Convert to kobo
                'recipient': recipient_code,
                'reason': reason
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            response_data = response.json()
            
            if response_data.get('status'):
                return {
                    'success': True,
                    'transfer_code': response_data['data']['transfer_code'],
                    'reference': response_data['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Transfer failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error initiating transfer: {str(e)}'
            }