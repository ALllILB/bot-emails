import os
import sys
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def load_config() -> Dict:
    """Load configuration from environment variables with validation."""
    try:
        # Email accounts configuration
        accounts = []
        for i in range(1, 3):  # Support up to 2 accounts
            host = os.getenv(f'EMAIL{i}_HOST')
            user = os.getenv(f'EMAIL{i}_USER')
            password = os.getenv(f'EMAIL{i}_PASS')
            name = os.getenv(f'EMAIL{i}_NAME')
            
            if all([host, user, password, name]):
                accounts.append({
                    'name': name,
                    'host': host,
                    'user': user,
                    'pass': password
                })
        
        if not accounts:
            raise ValueError("No email accounts configured")
        
        # WhatsApp API configuration
        api_key = os.getenv('WHATSAPP_API_KEY')
        token = os.getenv('WHATSAPP_TOKEN')
        group_id = os.getenv('WHATSAPP_GROUP_ID')
        
        if not all([api_key, token]):
            raise ValueError("WhatsApp API credentials not configured")
        
        # Authorized users
        authorized_users_str = os.getenv('AUTHORIZED_USERS', '')
        authorized_users = [user.strip() for user in authorized_users_str.split(',') if user.strip()]
        
        return {
            'ACCOUNTS': accounts,
            'API_SETTINGS': {
                'API_KEY': api_key,
                'TOKEN': token,
                'GROUP_ID': group_id,
                'SEND_MESSAGE_ENDPOINT': f'https://api.whatsiplus.com/sendMsg/{api_key}',
                'GROUP_ENDPOINT': f'https://api.whatsiplus.com/sendGroup/{api_key}'
            },
            'AUTHORIZED_USERS': authorized_users,
            'FLASK_CONFIG': {
                'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
                'HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
                'PORT': int(os.getenv('FLASK_PORT', '8223'))
            }
        }
    
    except (ValueError, TypeError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)