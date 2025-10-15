from drf_yasg import openapi
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.utils import timezone
import requests
import logging

from .models import Visitor
from .serializers import (
    VisitorSerializer, 
    VisitorCreateSerializer, 
    VisitorUpdateSerializer
)
from apps.utils.telegram import telegram_service

logger = logging.getLogger(__name__)


class VisitorViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [AllowAny]  # Barcha endpointlar uchun authentication talab qilinmaydi
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VisitorCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VisitorUpdateSerializer
        return VisitorSerializer
    
    @swagger_auto_schema(
        request_body=VisitorCreateSerializer,
        responses={
            201: openapi.Response("Kursga ro'yxatdan o'tish muvaffaqiyatli amalga oshirildi"),
            400: openapi.Response("Validation xatosi")
        },
        operation_description="Kursga ro'yxatdan o'tish arizasini yaratadi va Telegram guruhiga xabar yuboradi"
    )
    def create(self, request, *args, **kwargs):
        """Create a new visitor registration and send Telegram notification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visitor = serializer.save()
        
        # Send Telegram notification
        self.send_telegram_notification(visitor)
        
        return_serializer = VisitorSerializer(visitor)
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        responses={
            200: VisitorSerializer,
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Barcha kursga ro'yxatdan o'tgan foydalanuvchilarni qaytaradi"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        responses={
            200: VisitorSerializer,
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Kursga ro'yxatdan o'tgan foydalanuvchi ma'lumotlarini qaytaradi"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        request_body=VisitorUpdateSerializer,
        responses={
            200: VisitorSerializer,
            400: openapi.Response("Validation xatosi"),
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Kursga ro'yxatdan o'tgan foydalanuvchi holatini yangilaydi"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def send_telegram_notification(self, visitor):
        """Send notification to Telegram group about new registration"""
        try:
            # Tashkent vaqti bilan ko'rsatish
            tashkent_time = timezone.localtime(visitor.created_at, timezone=timezone.get_fixed_timezone(300))  # UTC+5
            formatted_time = tashkent_time.strftime('%d.%m.%Y %H:%M')
            
            logger.info(f"Sending visitor notification for visitor {visitor.id}: {visitor.full_name}")
            
            # Use centralized telegram service
            success = telegram_service.send_visitor_notification(
                full_name=visitor.full_name,
                phone_number=visitor.phone_number,
                date=formatted_time,
                visitor_id=visitor.id,
                admin_url="https://api.turantalim.uz/admin"
            )
            
            if success:
                logger.info(f"Telegram notification sent successfully for visitor {visitor.id}")
            else:
                logger.warning(f"Failed to send Telegram notification for visitor {visitor.id}")
            
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification for visitor {visitor.id}: {str(e)}", exc_info=True)
    
    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['new', 'in_review', 'approved'],
                    description='Yangi holat'
                )
            }
        ),
        responses={
            200: VisitorSerializer,
            400: openapi.Response("Noto'g'ri status"),
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Kursga ro'yxatdan o'tgan foydalanuvchi holatini o'zgartiradi"
    )
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change visitor status"""
        visitor = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Visitor.StatusChoices.choices):
            return Response(
                {'error': 'Noto\'g\'ri status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visitor.status = new_status
        visitor.save()
        
        serializer = self.get_serializer(visitor)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: openapi.Response(
                description="Statistika ma'lumotlari",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER, description='Jami foydalanuvchilar'),
                        'new': openapi.Schema(type=openapi.TYPE_INTEGER, description='Yangi arizalar'),
                        'in_review': openapi.Schema(type=openapi.TYPE_INTEGER, description='Ko\'rib chiqilmoqda'),
                        'approved': openapi.Schema(type=openapi.TYPE_INTEGER, description='Qabul qilinganlar'),
                    }
                )
            )
        },
        operation_description="Kursga ro'yxatdan o'tgan foydalanuvchilar statistikasini qaytaradi"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get visitor statistics"""
        total_visitors = Visitor.objects.count()
        new_visitors = Visitor.objects.filter(status=Visitor.StatusChoices.NEW).count()
        in_review_visitors = Visitor.objects.filter(status=Visitor.StatusChoices.IN_REVIEW).count()
        approved_visitors = Visitor.objects.filter(status=Visitor.StatusChoices.APPROVED).count()
        
        return Response({
            'total': total_visitors,
            'new': new_visitors,
            'in_review': in_review_visitors,
            'approved': approved_visitors
        })
    
    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Holat bo'yicha filtrlash",
                type=openapi.TYPE_STRING,
                enum=['new', 'in_review', 'approved'],
                required=False
            )
        ],
        responses={
            200: VisitorSerializer(many=True),
        },
        operation_description="Holat bo'yicha filtrlangan kursga ro'yxatdan o'tgan foydalanuvchilarni qaytaradi"
    )
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get visitors filtered by status"""
        status_filter = request.query_params.get('status')
        
        if status_filter:
            queryset = self.queryset.filter(status=status_filter)
        else:
            queryset = self.queryset
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
