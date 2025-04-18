# users/utils.py
import logging
import random
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

def generate_verification_code(length=6):
    """6 xonali tasdiqlash kodi generatsiya qilish"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email, code):
    """Email orqali tasdiqlash kodi yuborish (HTML formatida)"""
    subject = "Parolni tiklash uchun tasdiqlash kodi"
    
    # HTML shablonidan foydalanish
    html_content = render_to_string('emails/verification_code.html', {
        'code': code,
        'user_email': email,
        'expiration_minutes': 5
    })
    text_content = strip_tags(html_content)  # HTML dan oddiy matn versiyasini olish

    try:
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()
        logger.info(f"Tasdiqlash kodi email orqali yuborildi: {email}")
        return True
    except Exception as e:
        logger.error(f"Email yuborishda xatolik: {email} - {str(e)}")
        return False

def send_sms_via_eskiz(phone_number, code):
    """Eskiz orqali SMS yuborish"""
    url = "https://notify.eskiz.uz/api/message/sms/send"
    headers = {
        "Authorization": f"Bearer {settings.ESKIZ_TOKEN}"
    }
    data = {
        "mobile_phone": phone_number,
        "message": f"Sizning tasdiqlash kodingiz: {code}",
        "from": "4546",
        "callback_url": "http://your-api/sms-callback/"
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        logger.info(f"SMS yuborildi: {phone_number}")
        return True
    except requests.RequestException as e:
        logger.error(f"SMS yuborishda xatolik: {phone_number} - {str(e)}")
        return False