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

from django.contrib.auth import get_user_model
from apps.users.utils import send_sms_via_eskiz, generate_verification_code
from apps.users.models import VerificationCode
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

print("=== API Conditions Test Script ===")

User = get_user_model()

# Simulate the exact same logic as the API view
identifier = "+998908400751"
print(f"Processing identifier: {identifier}")

user = None
if identifier.startswith('+998'):
    user = User.objects.filter(phone=identifier).first()
else:
    user = User.objects.filter(email=identifier).first()
    
print(f"User found: {user}")
if user:
    print(f"User details: {user.username}, {user.phone}, {user.email}")

if not user:
    print("User not found - should return 404")
else:
    print("User found - proceeding with SMS")
    
    # Generate code
    code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=3)
    print(f"Generated code: {code}")
    
    # Delete old codes
    VerificationCode.objects.filter(user=user, is_used=False).delete()
    
    # Save new code
    VerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=expires_at
    )
    print("Verification code saved to database")
    
    # Send SMS
    if identifier.startswith('+998'):
        print("Attempting to send SMS")
        sms_sent = send_sms_via_eskiz(identifier, code)
        print(f"SMS sending result: {sms_sent}")
        if not sms_sent:
            print("SMS sending failed")
        else:
            print("SMS sent successfully")

