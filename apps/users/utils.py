# users/utils.py
import random
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.settings import base as settings
import requests
import logging

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
        'expiration_minutes': 3
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
        return True
    except Exception as e:
        return False


def refresh_eskiz_token():
    """Eskiz tokenini yangilash"""
    try:
        url = "https://notify.eskiz.uz/api/auth/refresh"
        headers = {
            "Authorization": f"Bearer {settings.ESKIZ_TOKEN}"
        }
        
        response = requests.patch(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            new_token = response_data.get('data', {}).get('token')
            if new_token:
                # Yangi tokenni settings ga saqlash
                settings.ESKIZ_TOKEN = new_token
                logger.info("Eskiz token muvaffaqiyatli yangilandi")
                return True
            else:
                logger.error("Eskiz token yangilashda token topilmadi")
                return False
        else:
            logger.error(f"Eskiz token yangilashda xatolik: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Eskiz token yangilashda network xatolik: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Eskiz token yangilashda kutilmagan xatolik: {str(e)}")
        return False


def send_sms_via_eskiz(phone_number, code):
    """Eskiz.uz orqali SMS yuborish"""
    
    # ESKIZ_TOKEN mavjudligini tekshirish
    if not hasattr(settings, 'ESKIZ_TOKEN') or not settings.ESKIZ_TOKEN:
        logger.error("ESKIZ_TOKEN topilmadi")
        return False

    url = "https://notify.eskiz.uz/api/message/sms/send"
    headers = {
        "Authorization": f"Bearer {settings.ESKIZ_TOKEN}"
    }
    cleaned_phone = phone_number.replace("+", "").replace(" ", "")
    data = {
        "mobile_phone": cleaned_phone,
        "message": f"Sizning https://turantalim.uz sahifasida parolni yangilash uchun tasdiqlash kodingiz: {code}.",
        "from": "4546",
        "callback_url": getattr(settings, 'ESKIZ_CALLBACK_URL', "") or ""
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 401:
            # Token eskirgan, yangilashni urinib ko'rish
            logger.warning("Eskiz token eskirgan, yangilash urinilmoqda...")
            if refresh_eskiz_token():
                # Yangi token bilan qayta urinish
                headers["Authorization"] = f"Bearer {settings.ESKIZ_TOKEN}"
                response = requests.post(url, headers=headers, data=data, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('status') == 'success' or response_data.get('status') == 'waiting':
                        return True
                    else:
                        logger.error(f"SMS yuborishda xatolik (token yangilangandan keyin): {response_data}")
                        return False
                else:
                    logger.error(f"SMS yuborishda xatolik (token yangilangandan keyin): {response.status_code}")
                    return False
            else:
                logger.error("Eskiz token yangilanmadi")
                return False
        elif response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'success' or response_data.get('status') == 'waiting':
                return True
            else:
                logger.error(f"SMS yuborishda xatolik: {response_data}")
                return False
        else:
            logger.error(f"SMS yuborishda xatolik: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"SMS yuborishda network xatolik: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"SMS yuborishda kutilmagan xatolik: {str(e)}")
        return False
