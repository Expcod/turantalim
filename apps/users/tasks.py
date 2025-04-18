# users/tasks.py
from celery import shared_task
from .utils import send_verification_email

@shared_task
def send_verification_email_task(email, code):
    return send_verification_email(email, code)