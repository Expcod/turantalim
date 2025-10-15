from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.logger import setup_logger
from database import Student, Submission, get_session
from keyboards.reply import get_student_menu

# Initialize logger
logger = setup_logger(__name__)

# Create router
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command for students"""
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    
    # Get database session
    session = await anext(get_session())
    
    # Check if user is already registered as a student
    student = await session.query(Student).filter(Student.telegram_id == user_id).first()
    
    if student:
        await message.answer(
            f"Welcome back, {user_full_name}! Your Telegram account is linked to TuranTalim system.",
            reply_markup=get_student_menu()
        )
    else:
        await message.answer(
            f"Welcome, {user_full_name}! To view your exam results, please link your Telegram account "
            f"with your TuranTalim account on the website."
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command for students"""
    help_text = (
        "TuranTalim Student Bot - Help\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/results - View your exam results\n"
        "/support - Contact support\n\n"
        "You will be notified here when your writing or speaking submissions are reviewed."
    )
    await message.answer(help_text, reply_markup=get_student_menu())

@router.message(Command("results"))
@router.message(F.text == "🔍 My Results")
async def cmd_results(message: Message):
    """Handle /results command and 'My Results' button"""
    user_id = message.from_user.id
    
    # Get database session
    session = await anext(get_session())
    
    # Check if user is registered
    student = await session.query(Student).filter(Student.telegram_id == user_id).first()
    
    if not student:
        await message.answer(
            "Your Telegram account is not linked to TuranTalim. "
            "Please link your account on the website to view your results."
        )
        return
    
    # Get student's submissions
    submissions = await session.query(Submission).filter(
        Submission.student_id == student.id,
        Submission.status == "completed"
    ).order_by(Submission.updated_at.desc()).limit(5).all()
    
    if not submissions:
        await message.answer("You don't have any reviewed submissions yet.")
        return
    
    # Show recent results
    results_text = "📝 Your recent results:\n\n"
    
    for submission in submissions:
        results_text += (
            f"📌 {submission.section.capitalize()} Submission\n"
            f"Date: {submission.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Score: {submission.score}/100\n"
            f"Feedback: {submission.feedback or 'No feedback provided'}\n\n"
        )
    
    results_text += "To see all results, please visit the TuranTalim website."
    
    await message.answer(results_text)

@router.message(Command("support"))
@router.message(F.text == "📞 Contact Support")
async def cmd_support(message: Message):
    """Handle /support command and 'Contact Support' button"""
    support_text = (
        "If you need help with your TuranTalim account or have questions about your exam results, "
        "please contact our support team:\n\n"
        "✉️ Email: support@turantalim.com\n"
        "☎️ Phone: +998 XX XXX XX XX\n"
        "🌐 Website: turantalim.com/support"
    )
    await message.answer(support_text)

# Function to notify student about reviewed submission
async def notify_student(user_id: int, score: int, feedback: str, section: str):
    """
    Notify student about their reviewed submission
    
    Args:
        user_id: Telegram user ID of student
        score: Review score
        feedback: Teacher feedback
        section: Section type (writing or speaking)
    """
    try:
        # Get bot instance
        from aiogram import Bot
        bot = Bot(token=Config.BOT_TOKEN)
        
        # Prepare notification message
        notification = (
            f"📢 Your {section.capitalize()} submission has been reviewed!\n\n"
            f"Score: {score}/100\n\n"
            f"Feedback: {feedback or 'No feedback provided'}\n\n"
            f"You can view all your results on the TuranTalim website."
        )
        
        # Send message
        await bot.send_message(user_id, notification)
        await bot.session.close()
        
        logger.info(f"Notification sent to student {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to student {user_id}: {e}")
        return False
