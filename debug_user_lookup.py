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
from django.db import connection
from apps.users.models import User, VerificationCode

print("=== User Lookup Debug Script ===")

User = get_user_model()

# Test database connection
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Database engine: {connection.settings_dict['ENGINE']}")

# Test user lookup
phone = "+998908400751"
print(f"Looking for user with phone: {phone}")

try:
    # Method 1: Direct filter
    user1 = User.objects.filter(phone=phone).first()
    print(f"Method 1 (filter): {user1}")
    
    # Method 2: Get all users and check
    all_users = User.objects.all()
    print(f"Total users in database: {all_users.count()}")
    
    # Method 3: Check each user's phone
    for user in all_users:
        print(f"User: {user.username}, Phone: '{user.phone}', Email: {user.email}")
        if user.phone == phone:
            print(f"Found matching user: {user}")
    
    # Method 4: Try exact match
    user2 = User.objects.filter(phone__exact=phone).first()
    print(f"Method 2 (exact): {user2}")
    
    # Method 5: Try case-insensitive
    user3 = User.objects.filter(phone__iexact=phone).first()
    print(f"Method 3 (iexact): {user3}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

