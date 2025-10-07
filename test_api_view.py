#!/usr/bin/env python3
import os
import sys
import django
import json

# Add the project directory to Python path
sys.path.append('/home/user/turantalim')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Setup Django
django.setup()

from django.test import RequestFactory
from apps.users.views import PasswordResetRequestView
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

print("=== API View Debug Script ===")

# Create a test request with proper DRF format
factory = APIRequestFactory()
data = {"identifier": "+998908400751"}
request = factory.post('/user/password/reset/request/', data, format='json')

# Create the view instance
view = PasswordResetRequestView()

try:
    # Call the view
    response = view.post(request)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
except Exception as e:
    print(f"API view error: {str(e)}")
    import traceback
    traceback.print_exc()
