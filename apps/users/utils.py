import requests
import smtplib
from email.mime.text import MIMEText
from django.conf import settings

# 1. SMS Yuborish (muloqot uchun API kerak bo‘ladi)
def send_sms(phone_number, message):
    API_URL = "https://api.smsprovider.uz/send"  # SMS provider API
    API_KEY = "SIZNING_API_KALITINGIZ"  # O'zingizning API kalitingizni qo'shing

    payload = {
        "phone": phone_number,
        "message": message,
        "key": API_KEY
    }

    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"SMS yuborishda xatolik: {response.text}")
            return False
    except Exception as e:
        print(f"SMS jo‘natishda xatolik: {str(e)}")
        return False

# 2. Email Yuborish (SMTP orqali)
def send_email(to_email, subject, message):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = settings.EMAIL_HOST_USER  # Django settings faylidan olamiz
    SMTP_PASS = settings.EMAIL_HOST_PASSWORD  # Django settings faylidan olamiz

    msg = MIMEText(message, "plain")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email jo‘natishda xatolik: {str(e)}")
        return False
