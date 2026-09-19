import requests
import json
from decimal import Decimal


class KhaltiPaymentService:
    """
    Service for handling Khalti payment integration
    """
    
    # Sandbox environment for testing
    SANDBOX_BASE_URL = "https://dev.khalti.com/api/v2"
    # Production environment
    PRODUCTION_BASE_URL = "https://a.khalti.com/api/v2"
    
    def __init__(self):
        # Lazy import to avoid circular dependency
        from django.conf import settings
        self.secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        self.public_key = getattr(settings, 'KHALTI_PUBLIC_KEY', 'test_public_key')
        
        # Determine base URL based on payment mode
        payment_mode = getattr(settings, 'PAYMENT_MODE', 'test')
        if payment_mode == 'sandbox':
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.PRODUCTION_BASE_URL
    
    def initiate_payment(self, amount, product_identity, product_name, callback_url, **kwargs):
        """
        Initiate a payment via Khalti
        
        Args:
            amount: Payment amount in paisa (1 NPR = 100 paisa)
            product_identity: Unique identifier for the product/service
            product_name: Name of the product/service
            callback_url: URL where Khalti will send payment confirmation
            **kwargs: Additional parameters (return_url, website_url, etc.)
        
        Returns:
            dict: Response from Khalti API
        """
        url = f"{self.base_url}/epayment/initiate/"
        
        headers = {
            'Authorization': f'Key {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        # Khalti API required format
        payload = {
            'amount': int(amount* 100),  # Convert to paisa
            'purchase_order_id': product_identity,
            'purchase_order_name': product_name,
            'return_url': kwargs.get('return_url', callback_url),
            'website_url': kwargs.get('website_url', 'http://127.0.0.1:8000/'),
        }
        
        # Add optional parameters
        if 'product_url' in kwargs:
            payload['product_url'] = kwargs['product_url']
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Khalti API Request: {payload}")
            print(f"Khalti API Response Status: {response.status_code}")
            print(f"Khalti API Response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # Khalti API response format: {'payment_url': '...', 'pidx': '...'}
            # Return in a consistent format
            if 'payment_url' in data:
                return {
                    'success': True,
                    'payment_url': data['payment_url'],
                    'pidx': data.get('pidx', ''),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'message': 'No payment URL in response',
                    'data': data
                }
        except requests.exceptions.RequestException as e:
            print(f"Khalti API Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to initiate payment'
            }
    
    def verify_payment(self, pidx, amount):
        """
        Verify a payment transaction
        
        Args:
            pidx: Payment index from Khalti
            amount: Expected amount in paisa
        
        Returns:
            dict: Verification result
        """
        url = f"{self.base_url}/epayment/lookup/"
        
        headers = {
            'Authorization': f'Key {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'pidx': pidx,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Check if payment is completed and amount matches
            if data.get('status') == 'Completed':
                return {
                    'success': True,
                    'transaction_id': data.get('transaction_id', pidx),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'message': f"Payment status: {data.get('status', 'Unknown')}",
                    'data': data
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to verify payment'
            }
    
    def get_payment_config(self):
        """
        Get Khalti payment configuration for frontend
        
        Returns:
            dict: Configuration data
        """
        return {
            'public_key': self.public_key,
            'base_url': self.base_url,
        }


def initiate_khalti_payment(amount, product_identity, product_name, callback_url, **kwargs):
    """
    Convenience function to initiate Khalti payment
    """
    service = KhaltiPaymentService()
    return service.initiate_payment(amount, product_identity, product_name, callback_url, **kwargs)


def verify_khalti_payment(pidx, amount):
    """
    Convenience function to verify Khalti payment
    """
    service = KhaltiPaymentService()
    return service.verify_payment(pidx, amount)