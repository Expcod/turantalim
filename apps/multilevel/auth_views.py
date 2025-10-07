"""
Authentication views for Admin Dashboard
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.conf import settings


class AdminLoginView(APIView):
    """
    Admin login endpoint for dashboard
    Accepts phone/username and password, returns DRF Token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        print(f"[DEBUG] Login attempt - Username: {username}")
        
        if not username or not password:
            return Response(
                {'error': 'Username va password talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate with phone or email
        from apps.users.models import User
        user = None
        
        # Try with phone first
        try:
            user_obj = User.objects.get(phone=username)
            print(f"[DEBUG] User found with phone: {user_obj.phone}, is_staff: {user_obj.is_staff}, is_active: {user_obj.is_active}")
            if user_obj.check_password(password):
                print(f"[DEBUG] Password correct!")
                user = user_obj
            else:
                print(f"[DEBUG] Password incorrect!")
        except User.DoesNotExist:
            print(f"[DEBUG] User not found with phone: {username}")
            # Try with email
            try:
                user_obj = User.objects.get(email=username)
                print(f"[DEBUG] User found with email: {user_obj.email}")
                if user_obj.check_password(password):
                    user = user_obj
            except User.DoesNotExist:
                print(f"[DEBUG] User not found with email: {username}")
                pass
        
        if user is not None:
            # Check if user is staff/admin
            if not user.is_staff:
                print(f"[DEBUG] User is not staff!")
                return Response(
                    {'error': 'Sizda admin panelga kirish huquqi yo\'q'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            print(f"[DEBUG] Token created/retrieved: {token.key[:10]}...")
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': getattr(user, 'username', user.phone),
                    'phone': user.phone,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                }
            }, status=status.HTTP_200_OK)
        else:
            print(f"[DEBUG] Authentication failed - user is None")
            return Response(
                {'error': 'Noto\'g\'ri login yoki parol'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class AdminLogoutView(APIView):
    """
    Admin logout endpoint - deletes the token
    """
    
    def post(self, request):
        if request.user.is_authenticated:
            try:
                # Delete the token
                Token.objects.filter(user=request.user).delete()
            except Exception:
                pass
        
        return Response(
            {'message': 'Muvaffaqiyatli chiqildi'},
            status=status.HTTP_200_OK
        )
