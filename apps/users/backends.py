# apps/users/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    """
    Telefon raqami yoki email orqali autentifikatsiya qilish uchun backend
    """
    def authenticate(self, request, phone=None, email=None, password=None, **kwargs):
        if phone:
            try:
                user = User.objects.get(phone=phone)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        elif email:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        return None
