from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error logging and debugging
    """
    # Get the standard error response
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error details
        request = context.get('request')
        view = context.get('view')
        
        logger.error(f"API Error: {exc.__class__.__name__}")
        logger.error(f"URL: {request.path if request else 'Unknown'}")
        logger.error(f"Method: {request.method if request else 'Unknown'}")
        logger.error(f"Headers: {dict(request.headers) if request else {}}")
        logger.error(f"User: {request.user if request and hasattr(request, 'user') else 'Anonymous'}")
        logger.error(f"Error: {str(exc)}")
        
        # Customize error response for authentication issues
        if response.status_code == 401:
            logger.error("Authentication failed - checking token format")
            if request and 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                logger.error(f"Auth header: {auth_header}")
                if not auth_header.startswith('Bearer '):
                    logger.error("Token format error: Missing 'Bearer ' prefix")
                    response.data = {
                        'error': 'Token format xatosi. Bearer prefix kerak.',
                        'detail': 'Authorization header "Bearer " bilan boshlanishi kerak.',
                        'example': 'Authorization: Bearer your_token_here'
                    }
                else:
                    token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else ''
                    if not token:
                        logger.error("Token format error: Empty token")
                        response.data = {
                            'error': 'Token format xatosi. Token bo\'sh.',
                            'detail': 'Authorization header da token bo\'sh.',
                            'example': 'Authorization: Bearer your_token_here'
                        }
                    else:
                        logger.error("Token validation failed - token may be expired or invalid")
                        response.data = {
                            'error': 'Token validation xatosi.',
                            'detail': 'Token muddati tugagan yoki noto\'g\'ri.',
                            'suggestion': 'Yangilangan token olish uchun /user/login/ endpoint\'dan foydalaning.'
                        }
            else:
                logger.error("Authentication failed: No Authorization header")
                response.data = {
                    'error': 'Authentication kerak.',
                    'detail': 'Authorization header yuborilmagan.',
                    'example': 'Authorization: Bearer your_token_here'
                }
    
    return response
