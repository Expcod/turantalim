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

from rest_framework.test import APIRequestFactory
from apps.users.views import PasswordResetRequestView
import json

print("=== Simple API Test ===")

# Create a test request
factory = APIRequestFactory()

# Test 1: Simple request
print("Test 1: Simple request")
data = {"identifier": "+998908400751"}
request = factory.post('/user/password/reset/request/', data, format='json')

view = PasswordResetRequestView()
try:
    response = view.post(request)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nTest 2: Request with explicit content type")
# Test 2: Request with explicit content type
request2 = factory.post(
    '/user/password/reset/request/', 
    json.dumps(data), 
    content_type='application/json'
)

try:
    response2 = view.post(request2)
    print(f"Response status: {response2.status_code}")
    print(f"Response data: {response2.data}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

