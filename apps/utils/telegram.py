"""
Telegram notification utility module
Provides centralized Telegram message sending functionality with proper error handling and logging
"""
import logging
import requests
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Service class for sending Telegram notifications"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.payment_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.visitor_chat_id = getattr(settings, 'TELEGRAM_VISITOR_CHAT_ID', None)
        self.timeout = 10  # seconds
        
    def is_configured(self, chat_type: str = 'payment') -> bool:
        """
        Check if Telegram bot is properly configured
        
        Args:
            chat_type: Type of chat ('payment' or 'visitor')
            
        Returns:
            bool: True if configured, False otherwise
        """
        if not self.bot_token:
            logger.warning("Telegram bot token is not configured")
            return False
            
        if chat_type == 'payment' and not self.payment_chat_id:
            logger.warning("Payment chat ID is not configured")
            return False
            
        if chat_type == 'visitor' and not self.visitor_chat_id:
            logger.warning("Visitor chat ID is not configured")
            return False
            
        return True
    
    def send_message(
        self, 
        message: str, 
        chat_id: Optional[str] = None,
        parse_mode: str = 'HTML'
    ) -> bool:
        """
        Send a message to Telegram
        
        Args:
            message: Message text to send
            chat_id: Chat ID (if None, uses payment chat)
            parse_mode: Parse mode for the message (HTML or Markdown)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bot_token:
            logger.error("Cannot send Telegram message: bot token not configured")
            return False
            
        target_chat_id = chat_id or self.payment_chat_id
        if not target_chat_id:
            logger.error("Cannot send Telegram message: chat ID not provided")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': target_chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            logger.info(f"Sending Telegram message to chat {target_chat_id}")
            logger.debug(f"Message content: {message[:100]}...")
            
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info(f"Telegram message sent successfully. Message ID: {result.get('result', {}).get('message_id')}")
                return True
            else:
                logger.error(f"Telegram API returned error: {result.get('description')}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while sending Telegram message to {target_chat_id}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}", exc_info=True)
            return False
    
    def send_payment_notification(
        self,
        user_name: str,
        amount: float,
        payment_type: str,
        current_balance: Optional[float] = None,
        payment_method: str = "Payme",
        date: Optional[str] = None
    ) -> bool:
        """
        Send payment notification to payment group
        
        Args:
            user_name: Name of the user
            amount: Payment amount
            payment_type: Type of payment (e.g., "Balans To'ldirish", "Imtihon To'lovi")
            current_balance: Current balance after transaction
            payment_method: Payment method used
            date: Payment date
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_configured('payment'):
            return False
            
        message_lines = [
            f"✅ {payment_type}!",
            f"👤 Foydalanuvchi: {user_name}",
            f"💰 Miqdor: {amount:,.0f} UZS",
        ]
        
        if current_balance is not None:
            message_lines.append(f"💳 Joriy Balans: {current_balance:,.0f} UZS")
            
        message_lines.append(f"💳 To'lov usuli: {payment_method}")
        
        if date:
            message_lines.append(f"📅 Sana: {date}")
            
        message = "\n".join(message_lines)
        return self.send_message(message, self.payment_chat_id)
    
    def send_visitor_notification(
        self,
        full_name: str,
        phone_number: str,
        date: str,
        visitor_id: int,
        admin_url: str = "https://api.turantalim.uz/admin"
    ) -> bool:
        """
        Send visitor registration notification to visitor group
        
        Args:
            full_name: Visitor's full name
            phone_number: Visitor's phone number
            date: Registration date
            visitor_id: Visitor's ID
            admin_url: Base URL for admin panel
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_configured('visitor'):
            return False
            
        message = f"""🆕 Yangi kursga ro'yxatdan o'tish arizasi!

👤 Foydalanuvchi: {full_name}
📱 Telefon: {phone_number}
📅 Sana: {date}
🔗 Admin panel: {admin_url}/visitor/visitor/{visitor_id}/"""
        
        return self.send_message(message, self.visitor_chat_id)
    
    def test_connection(self, chat_type: str = 'payment') -> dict:
        """
        Test bot connection and permissions
        
        Args:
            chat_type: Type of chat to test ('payment' or 'visitor')
            
        Returns:
            dict: Test results with status and details
        """
        result = {
            'configured': False,
            'bot_valid': False,
            'can_send_message': False,
            'error': None
        }
        
        # Check configuration
        if not self.is_configured(chat_type):
            result['error'] = f"Bot not configured for {chat_type}"
            return result
        result['configured'] = True
        
        # Check bot token
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            bot_info = response.json()
            
            if bot_info.get('ok'):
                result['bot_valid'] = True
                result['bot_username'] = bot_info.get('result', {}).get('username')
            else:
                result['error'] = f"Bot token invalid: {bot_info.get('description')}"
                return result
        except Exception as e:
            result['error'] = f"Cannot verify bot: {str(e)}"
            return result
        
        # Test sending message
        chat_id = self.visitor_chat_id if chat_type == 'visitor' else self.payment_chat_id
        test_message = f"🔔 Test xabari - {chat_type} notification system is working!"
        
        if self.send_message(test_message, chat_id):
            result['can_send_message'] = True
        else:
            result['error'] = "Cannot send message to group. Check if bot is admin."
            
        return result


# Global instance
telegram_service = TelegramNotificationService()

