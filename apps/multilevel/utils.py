# multilevel/utils.py
import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


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


def send_exam_result_sms(phone_number, exam_name=None):
    """Imtihon natijasi tayyor bo'lgani haqida SMS yuborish"""
    
    # ESKIZ_TOKEN mavjudligini tekshirish
    if not hasattr(settings, 'ESKIZ_TOKEN') or not settings.ESKIZ_TOKEN:
        logger.error("ESKIZ_TOKEN topilmadi")
        return False

    url = "https://notify.eskiz.uz/api/message/sms/send"
    headers = {
        "Authorization": f"Bearer {settings.ESKIZ_TOKEN}"
    }
    cleaned_phone = phone_number.replace("+", "").replace(" ", "")
    
    # SMS matnini tayyorlash
    message = "Hurmatli talaba! turantalim.uz saytida topshirgan yangi imtihoningiz natijasini profilizda ko'rishingiz mumkin bo'ladi."
    
    data = {
        "mobile_phone": cleaned_phone,
        "message": message,
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
                        logger.info(f"Imtihon natijasi SMS muvaffaqiyatli yuborildi: {cleaned_phone}")
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
                logger.info(f"Imtihon natijasi SMS muvaffaqiyatli yuborildi: {cleaned_phone}")
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


def send_exam_result_notification(user_test):
    """Imtihon natijasi tayyor bo'lgani haqida foydalanuvchiga xabar yuborish"""
    try:
        # Foydalanuvchining telefon raqamini olish
        phone_number = user_test.user.phone
        
        if not phone_number:
            logger.warning(f"Foydalanuvchi {user_test.user.id} da telefon raqami yo'q")
            return False
        
        # SMS yuborish
        success = send_exam_result_sms(phone_number, user_test.exam.title)
        
        if success:
            logger.info(f"Imtihon natijasi SMS foydalanuvchi {user_test.user.id} ga yuborildi")
            return True
        else:
            logger.error(f"Imtihon natijasi SMS foydalanuvchi {user_test.user.id} ga yuborilmadi")
            return False
            
    except Exception as e:
        logger.error(f"Imtihon natijasi xabari yuborishda xatolik: {str(e)}")
        return False


def test_sms_notification(phone_number):
    """SMS xabar yuborish funksiyasini test qilish"""
    try:
        success = send_exam_result_sms(phone_number)
        if success:
            logger.info(f"Test SMS muvaffaqiyatli yuborildi: {phone_number}")
            return True
        else:
            logger.error(f"Test SMS yuborilmadi: {phone_number}")
            return False
    except Exception as e:
        logger.error(f"Test SMS yuborishda xatolik: {str(e)}")
        return False


def check_test_time_limit(test_result):
    """
    Test vaqt chegarasini tekshirish
    
    Args:
        test_result: TestResult obyekti
        
    Returns:
        bool: True agar vaqt tugagan bo'lsa, False aks holda
    """
    try:
        if not test_result.end_time:
            return False
            
        now = timezone.now()
        
        # Agar vaqt tugagan bo'lsa
        if now >= test_result.end_time:
            # Testni completed holatiga o'tkazish
            if test_result.status == 'started':
                test_result.status = 'completed'
                test_result.save()
                logger.info(f"Test {test_result.id} vaqt chegarasi tugagani uchun avtomatik yakunlandi")
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Test vaqt chegarasini tekshirishda xatolik: {str(e)}")
        return False


def schedule_test_time_limit(test_result):
    """
    Test uchun vaqt chegarasi task'ini rejalashtirish
    
    Args:
        test_result: TestResult obyekti
    """
    try:
        from .tasks import auto_complete_test
        
        if not test_result.end_time:
            logger.warning(f"Test {test_result.id} uchun end_time belgilanmagan")
            return False
        
        # Vaqt chegarasi tugaganda task'ni ishga tushirish
        eta = test_result.end_time
        task = auto_complete_test.apply_async(args=[test_result.id], eta=eta)
        
        logger.info(f"Test {test_result.id} uchun vaqt chegarasi rejalashtirildi: {eta}")
        return True
        
    except Exception as e:
        logger.error(f"Test vaqt chegarasi rejalashtirishda xatolik: {str(e)}")
        return False