#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/user/turantalim')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Setup Django
django.setup()

from django.conf import settings
from apps.users.utils import send_sms_via_eskiz, generate_verification_code
import requests

print("=== SMS Debug Script ===")
print(f"ESKIZ_TOKEN: {getattr(settings, 'ESKIZ_TOKEN', 'NOT_SET')[:20]}..." if getattr(settings, 'ESKIZ_TOKEN', None) else "ESKIZ_TOKEN: NOT_SET")
print(f"STAGE: {getattr(settings, 'STAGE', 'NOT_SET')}")

# Test SMS sending
phone = "+998908400751"
code = generate_verification_code()
print(f"Testing SMS to {phone} with code {code}")

try:
    result = send_sms_via_eskiz(phone, code)
    print(f"SMS result: {result}")
except Exception as e:
    print(f"SMS error: {str(e)}")
    import traceback
    traceback.print_exc()

