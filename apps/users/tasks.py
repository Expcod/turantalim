# users/tasks.py
from celery import shared_task
from .utils import send_verification_email, send_sms_via_eskiz

@shared_task
def send_verification_email_task(email, code):
    """Email orqali tasdiqlash kodi yuborish uchun asinxron task"""
    return send_verification_email(email, code)

@shared_task
def send_sms_task(phone_number, code):
    """SMS orqali tasdiqlash kodi yuborish uchun asinxron task"""
    return send_sms_via_eskiz(phone_number, code)
