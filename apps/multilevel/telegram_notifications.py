"""
Telegram Notifications for Manual Review System
Sends notifications to teachers' group when new submissions arrive
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone
import pytz

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send Telegram notifications for new submissions"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.teacher_group_id = getattr(settings, 'TELEGRAM_TEACHER_GROUP_ID', None)
        self.admin_id = getattr(settings, 'TELEGRAM_ADMIN_ID', None)
        
    def is_configured(self):
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.teacher_group_id)
    
    def _format_tashkent_dt(self, dt):
        """Format a timezone-aware datetime in Asia/Tashkent as dd.mm.yyyy HH:MM"""
        if not dt:
            return ""
        tz = pytz.timezone('Asia/Tashkent')
        local_dt = timezone.localtime(dt, tz)
        return local_dt.strftime('%d.%m.%Y %H:%M')

    def send_message(self, chat_id, message, parse_mode='HTML'):
        """Send a message to a specific chat and return message_id if successful"""
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return None
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            message_id = result.get('result', {}).get('message_id')
            logger.info(f"Telegram message sent successfully to {chat_id}, message_id: {message_id}")
            return message_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None
    
    def notify_new_submission(self, test_result, section='writing'):
        """
        Notify teachers group about new submission and return message_id
        
        Args:
            test_result: TestResult object
            section: 'writing' or 'speaking'
        
        Returns:
            message_id if successful, None otherwise
        """
        if not self.is_configured():
            logger.warning("Telegram notifications not configured")
            return None
        
        try:
            # Get user info
            user = test_result.user_test.user
            exam = test_result.user_test.exam
            
            # Format section name
            section_emoji = "✍️" if section == 'writing' else "🎤"
            section_name = "Writing" if section == 'writing' else "Speaking"
            
            # Format email
            email_text = user.email or 'Yoq'
            
            # Format datetime in Uzbekistan timezone
            end_time_str = self._format_tashkent_dt(test_result.end_time)
            
            # Build message
            message = f"""
🔔 <b>Yangi Imtihon Javobi!</b>

{section_emoji} <b>Bo'lim:</b> {section_name}

👤 <b>Talaba:</b> {user.get_full_name()}
📱 <b>Telefon:</b> {user.phone}
📧 <b>Email:</b> {email_text}

📝 <b>Imtihon:</b> {exam.title}
📊 <b>Level:</b> {exam.level.upper()}

🆔 <b>Test Result ID:</b> {test_result.id}
📅 <b>Topshirgan vaqti:</b> {end_time_str}

⏰ <b>Status:</b> Tekshirish kutilmoqda (Pending)

🔗 <b>Admin Dashboard:</b>
https://api.turantalim.uz/admin-dashboard/submission.html?id={test_result.id}

<i>Iltimos, imkon qadar tezroq tekshiring! ⚡</i>
            """.strip()
            
            # Send to teachers group and get message_id
            message_id = self.send_message(self.teacher_group_id, message)
            
            if message_id:
                logger.info(f"Notified teachers about {section} submission {test_result.id}, message_id: {message_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return None
    
    def notify_submission_checked(self, manual_review):
        """
        Notify when a submission has been checked (optional)
        This can be sent to the student or admin
        """
        if not self.is_configured():
            return False
        
        try:
            test_result = manual_review.test_result
            user = test_result.user_test.user
            exam = test_result.user_test.exam
            reviewer = manual_review.reviewer
            
            section_emoji = "✍️" if manual_review.section == 'writing' else "🎤"
            section_name = "Writing" if manual_review.section == 'writing' else "Speaking"
            
            # Format datetime in Uzbekistan timezone
            reviewed_at_str = self._format_tashkent_dt(manual_review.reviewed_at)
            reviewer_name = reviewer.get_full_name() if reviewer else 'Unknown'
            
            message = f"""
✅ <b>Imtihon Baholandi!</b>

{section_emoji} <b>Bo'lim:</b> {section_name}

👤 <b>Talaba:</b> {user.get_full_name()}
📝 <b>Imtihon:</b> {exam.title}

📊 <b>Ball:</b> {manual_review.total_score}/100
👨‍🏫 <b>Tekshiruvchi:</b> {reviewer_name}
📅 <b>Tekshirilgan vaqt:</b> {reviewed_at_str}

🆔 <b>Test Result ID:</b> {test_result.id}
            """.strip()
            
            # Send to admin (optional)
            if self.admin_id:
                self.send_message(self.admin_id, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
            return False
    
    def delete_message(self, chat_id, message_id):
        """Delete a message from a chat"""
        if not self.bot_token or not message_id:
            logger.warning("Cannot delete message: bot token or message_id not provided")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/deleteMessage"
        
        payload = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Telegram message {message_id} deleted successfully from {chat_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete Telegram message: {e}")
            return False
    
    def delete_submission_notification(self, manual_review):
        """Delete the notification message for a submission when it starts being reviewed"""
        if not self.is_configured():
            return False
        
        if not manual_review.telegram_message_id:
            logger.info(f"No telegram message_id found for manual_review {manual_review.id}")
            return False
        
        try:
            success = self.delete_message(self.teacher_group_id, manual_review.telegram_message_id)
            
            if success:
                logger.info(f"Deleted notification for submission {manual_review.test_result.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting submission notification: {e}")
            return False


# Global instance
telegram_notifier = TelegramNotifier()
