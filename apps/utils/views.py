"""
Health check and monitoring views for utilities
"""
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .telegram import telegram_service

logger = logging.getLogger(__name__)


class TelegramHealthCheckView(views.APIView):
    """
    Health check endpoint for Telegram bot connectivity
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Telegram bot ulanishini va guruhlar bilan ishlashni tekshiradi",
        operation_summary="Telegram Bot Health Check",
        manual_parameters=[
            openapi.Parameter(
                'chat_type',
                openapi.IN_QUERY,
                description="Tekshiriladigan guruh turi (payment yoki visitor). Default: ikkala guruh ham",
                type=openapi.TYPE_STRING,
                enum=['payment', 'visitor', 'all'],
                default='all'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Health check natijalari",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Umumiy holat'),
                        'payment_group': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'configured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'bot_valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'can_send_message': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'bot_username': openapi.Schema(type=openapi.TYPE_STRING),
                                'error': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'visitor_group': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'configured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'bot_valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'can_send_message': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'bot_username': openapi.Schema(type=openapi.TYPE_STRING),
                                'error': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                    }
                )
            ),
            403: openapi.Response("Ruxsat berilmagan"),
        }
    )
    def get(self, request):
        """
        Telegram bot health check
        Tests bot connectivity and group permissions
        """
        chat_type = request.query_params.get('chat_type', 'all')
        
        result = {
            'status': 'ok',
            'timestamp': None
        }
        
        # Test payment group
        if chat_type in ['payment', 'all']:
            logger.info("Testing payment group connectivity")
            payment_result = telegram_service.test_connection('payment')
            result['payment_group'] = payment_result
            
            if not payment_result.get('can_send_message'):
                result['status'] = 'partial'
        
        # Test visitor group
        if chat_type in ['visitor', 'all']:
            logger.info("Testing visitor group connectivity")
            visitor_result = telegram_service.test_connection('visitor')
            result['visitor_group'] = visitor_result
            
            if not visitor_result.get('can_send_message'):
                result['status'] = 'partial'
        
        # Overall status
        if chat_type == 'all':
            payment_ok = result.get('payment_group', {}).get('can_send_message', False)
            visitor_ok = result.get('visitor_group', {}).get('can_send_message', False)
            
            if not payment_ok and not visitor_ok:
                result['status'] = 'error'
            elif not payment_ok or not visitor_ok:
                result['status'] = 'partial'
        
        # Add timestamp
        from django.utils import timezone
        result['timestamp'] = timezone.now().isoformat()
        
        # Set HTTP status based on result
        http_status = 200
        if result['status'] == 'error':
            http_status = 500
        elif result['status'] == 'partial':
            http_status = 207  # Multi-Status
        
        return Response(result, status=http_status)

