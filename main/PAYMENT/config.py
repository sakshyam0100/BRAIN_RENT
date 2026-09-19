"""
Khalti Payment Configuration

Add these settings to your Django settings.py file:

KHALTI_PUBLIC_KEY = 'your_public_key'
KHALTI_SECRET_KEY = 'your_secret_key'

For testing, use Khalti's test credentials:
KHALTI_PUBLIC_KEY = 'test_public_key'
KHALTI_SECRET_KEY = 'test_secret_key'
"""

# Default test credentials (replace with your actual credentials)
DEFAULT_KHALTI_CONFIG = {
    'public_key': 'test_public_key',
    'secret_key': 'test_secret_key',
}

def get_khalti_config():
    """
    Get Khalti configuration from Django settings
    """
    from django.conf import settings
    
    return {
        'public_key': getattr(settings, 'KHALTI_PUBLIC_KEY', DEFAULT_KHALTI_CONFIG['public_key']),
        'secret_key': getattr(settings, 'KHALTI_SECRET_KEY', DEFAULT_KHALTI_CONFIG['secret_key']),
    }