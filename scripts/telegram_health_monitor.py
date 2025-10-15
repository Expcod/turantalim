#!/usr/bin/env python3
"""
Telegram Health Monitor Script
Bu script kuniga bir marta ishga tushib, Telegram bot va guruhlar holatini tekshiradi.
Agar muammo aniqlansa, admin ga xabar yuboradi va logga yozadi.

Cron job orqali ishga tushirish:
0 9 * * * cd /home/user/turantalim && source venv/bin/activate && python scripts/telegram_health_monitor.py >> logs/telegram_health.log 2>&1
"""

import os
import sys
import django
from datetime import datetime

# Django setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.utils.telegram import telegram_service


def check_health():
    """
    Telegram bot va guruhlar holatini tekshiradi
    """
    print(f"\n{'='*60}")
    print(f"Telegram Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    issues = []
    
    # Payment group tekshirish
    print("Checking Payment Group...")
    payment_result = telegram_service.test_connection('payment')
    
    if not payment_result.get('configured'):
        issues.append("❌ Payment group is not configured")
    elif not payment_result.get('bot_valid'):
        issues.append("❌ Payment bot token is invalid")
    elif not payment_result.get('can_send_message'):
        issues.append(f"❌ Cannot send message to payment group: {payment_result.get('error')}")
    else:
        print(f"✅ Payment group OK - Bot: @{payment_result.get('bot_username')}")
    
    # Visitor group tekshirish
    print("Checking Visitor Group...")
    visitor_result = telegram_service.test_connection('visitor')
    
    if not visitor_result.get('configured'):
        issues.append("❌ Visitor group is not configured")
    elif not visitor_result.get('bot_valid'):
        issues.append("❌ Visitor bot token is invalid")
    elif not visitor_result.get('can_send_message'):
        issues.append(f"❌ Cannot send message to visitor group: {visitor_result.get('error')}")
    else:
        print(f"✅ Visitor group OK - Bot: @{visitor_result.get('bot_username')}")
    
    # Natijalarni chiqarish
    print(f"\n{'='*60}")
    
    if issues:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print(f"\n{'='*60}\n")
        return False
    else:
        print("✅ All systems operational!")
        print(f"{'='*60}\n")
        return True


def main():
    """
    Main entry point
    """
    try:
        success = check_health()
        
        # Exit code: 0 = success, 1 = failure
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

