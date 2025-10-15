import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.logger import setup_logger
from utils.states import TeacherState, ScoreData
from utils.api import update_submission_status, update_submission_score, notify_student
from database import Teacher, Submission, get_session
from keyboards.reply import get_teacher_main_menu, get_score_keyboard, remove_keyboard
from keyboards.inline import get_submission_actions_keyboard, get_cancel_keyboard, get_confirm_score_keyboard

# Initialize logger
logger = setup_logger(__name__)

# Create router
router = Router()

# Helper for parsing callback data
def parse_callback_data(callback_data: str) -> tuple:
    """Parse callback data in format action:submission_id"""
    parts = callback_data.split(":")
    if len(parts) != 2:
        return None, None
    return parts[0], int(parts[1])

# Command handlers
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    
    # Get database session
    session = await anext(get_session())
    
    # Check if user is already registered as a teacher
    teacher = await Teacher.get_by_telegram_id(session, user_id)
    
    if not teacher:
        # Register new teacher
        teacher = Teacher(
            telegram_id=user_id,
            full_name=user_full_name,
            username=username
        )
        session.add(teacher)
        await session.commit()
        
        await message.answer(
            f"Welcome, {user_full_name}! You have been registered as a teacher in TuranTalim system.",
            reply_markup=get_teacher_main_menu()
        )
    else:
        await message.answer(
            f"Welcome back, {user_full_name}! You are already registered as a teacher.",
            reply_markup=get_teacher_main_menu()
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        "TuranTalim Teacher Bot - Help\n\n"
        "Available commands:\n"
        "/start - Start the bot and register as a teacher\n"
        "/help - Show this help message\n"
        "/pending - Show pending submissions\n"
        "/stats - Show your statistics\n\n"
        "Workflow:\n"
        "1. View pending submissions\n"
        "2. Mark a submission as 'Checking' while you review it\n"
        "3. Add score (0-100) and feedback\n"
        "4. Submit the review\n\n"
        "The student will be notified once you complete your review."
    )
    await message.answer(help_text, reply_markup=get_teacher_main_menu())

@router.message(Command("pending"))
@router.message(F.text == "📋 Pending Submissions")
async def cmd_pending_submissions(message: Message):
    """Handle /pending command and 'Pending Submissions' button"""
    # Get database session
    session = await anext(get_session())
    
    # Get pending submissions
    try:
        pending_submissions = await session.query(Submission).filter(Submission.status == "pending").all()
        
        if not pending_submissions:
            await message.answer("No pending submissions found.")
            return
        
        for submission in pending_submissions:
            # Get student info
            student = await submission.get_student
            
            # Format message based on section type
            if submission.section == "writing":
                content_info = f"Writing text:\n{submission.text[:200]}..."
            else:  # speaking
                content_info = f"Speaking audio file: {os.path.basename(submission.audio_path)}"
            
            submission_msg = (
                f"📝 New {submission.section.capitalize()} Submission\n\n"
                f"Student: {student.full_name}\n"
                f"Submission ID: {submission.id}\n"
                f"Created: {submission.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"{content_info}"
            )
            
            # Send message with action keyboard
            if submission.section == "speaking" and submission.audio_path:
                # Send audio file
                with open(submission.audio_path, 'rb') as audio:
                    await message.answer_audio(
                        audio,
                        caption=submission_msg,
                        reply_markup=get_submission_actions_keyboard(submission.id)
                    )
            else:
                # Send text only
                await message.answer(
                    submission_msg,
                    reply_markup=get_submission_actions_keyboard(submission.id)
                )
    except Exception as e:
        logger.error(f"Error fetching pending submissions: {e}")
        await message.answer(f"Error fetching pending submissions: {str(e)}")

@router.message(Command("stats"))
@router.message(F.text == "📊 My Statistics")
async def cmd_stats(message: Message):
    """Handle /stats command and 'My Statistics' button"""
    user_id = message.from_user.id
    
    # Get database session
    session = await anext(get_session())
    
    # Get teacher
    teacher = await Teacher.get_by_telegram_id(session, user_id)
    
    if not teacher:
        await message.answer("You are not registered as a teacher.")
        return
    
    # Get statistics
    try:
        checked_count = await session.query(Submission).filter(
            Submission.teacher_id == teacher.id, 
            Submission.status == "completed"
        ).count()
        
        writing_count = await session.query(Submission).filter(
            Submission.teacher_id == teacher.id,
            Submission.status == "completed",
            Submission.section == "writing"
        ).count()
        
        speaking_count = await session.query(Submission).filter(
            Submission.teacher_id == teacher.id,
            Submission.status == "completed",
            Submission.section == "speaking"
        ).count()
        
        stats_msg = (
            f"📊 Your Statistics\n\n"
            f"Total submissions checked: {checked_count}\n"
            f"Writing submissions: {writing_count}\n"
            f"Speaking submissions: {speaking_count}\n"
        )
        
        await message.answer(stats_msg)
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        await message.answer(f"Error fetching statistics: {str(e)}")

# Callback query handlers
@router.callback_query(lambda c: c.data.startswith("mark_checked:"))
async def process_mark_checked(callback_query: CallbackQuery):
    """Handle mark as checked button"""
    action, submission_id = parse_callback_data(callback_query.data)
    user_id = callback_query.from_user.id
    
    # Get database session
    session = await anext(get_session())
    
    # Get teacher
    teacher = await Teacher.get_by_telegram_id(session, user_id)
    
    if not teacher:
        await callback_query.answer("You are not registered as a teacher.")
        return
    
    # Update submission status
    try:
        # Update local database
        submission = await session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            await callback_query.answer("Submission not found.")
            return
        
        submission.status = "checking"
        submission.teacher_id = teacher.id
        await session.commit()
        
        # Update Django API
        response = await update_submission_status(submission_id, "checking", teacher.id)
        
        if not response.get("success"):
            logger.error(f"Error updating submission status in API: {response.get('error')}")
            await callback_query.answer("Error updating submission status in API.")
            return
        
        # Update message with new status
        await callback_query.message.edit_text(
            callback_query.message.text + "\n\n✏️ Status: Checking by " + teacher.full_name,
            reply_markup=get_submission_actions_keyboard(submission_id)
        )
        
        await callback_query.answer("Submission marked as 'checking'.")
    except Exception as e:
        logger.error(f"Error marking submission as checked: {e}")
        await callback_query.answer(f"Error: {str(e)}")

@router.callback_query(lambda c: c.data.startswith("add_score:"))
async def process_add_score(callback_query: CallbackQuery, state: FSMContext):
    """Handle add score button"""
    action, submission_id = parse_callback_data(callback_query.data)
    
    # Store submission ID in state
    await state.set_state(TeacherState.waiting_for_score)
    await state.update_data(submission_id=submission_id)
    
    await callback_query.message.reply(
        "Please enter a score (0-100) for this submission:",
        reply_markup=get_score_keyboard()
    )
    await callback_query.answer()

@router.message(TeacherState.waiting_for_score)
async def process_score_input(message: Message, state: FSMContext):
    """Handle score input"""
    # Check for cancel
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer(
            "Score submission cancelled.",
            reply_markup=get_teacher_main_menu()
        )
        return
    
    # Validate score
    try:
        score = int(message.text)
        if not (0 <= score <= 100):
            await message.answer(
                "Score must be between 0 and 100. Please try again:",
                reply_markup=get_score_keyboard()
            )
            return
    except ValueError:
        await message.answer(
            "Invalid score. Please enter a number between 0 and 100:",
            reply_markup=get_score_keyboard()
        )
        return
    
    # Store score in state
    await state.update_data(score=score)
    
    # Ask for feedback
    await message.answer(
        "Please enter feedback for this submission (or type 'skip' to leave blank):",
        reply_markup=remove_keyboard()
    )
    await state.set_state(TeacherState.waiting_for_feedback)

@router.message(TeacherState.waiting_for_feedback)
async def process_feedback_input(message: Message, state: FSMContext):
    """Handle feedback input"""
    # Get data from state
    data = await state.get_data()
    submission_id = data.get("submission_id")
    score = data.get("score")
    
    # Get feedback
    feedback = "" if message.text.lower() == "skip" else message.text
    
    # Show confirmation
    await message.answer(
        f"Please confirm the following submission:\n\n"
        f"Submission ID: {submission_id}\n"
        f"Score: {score}/100\n"
        f"Feedback: {feedback or '(No feedback provided)'}\n\n"
        f"Is this correct?",
        reply_markup=get_confirm_score_keyboard(submission_id)
    )
    
    # Store feedback in state
    await state.update_data(feedback=feedback)

@router.callback_query(lambda c: c.data.startswith("confirm_score:"))
async def process_confirm_score(callback_query: CallbackQuery, state: FSMContext):
    """Handle score confirmation"""
    action, submission_id = parse_callback_data(callback_query.data)
    user_id = callback_query.from_user.id
    
    # Get data from state
    data = await state.get_data()
    stored_submission_id = data.get("submission_id")
    score = data.get("score")
    feedback = data.get("feedback", "")
    
    # Verify submission ID
    if submission_id != stored_submission_id:
        await callback_query.answer("Error: Submission ID mismatch.")
        return
    
    # Get database session
    session = await anext(get_session())
    
    # Get teacher
    teacher = await Teacher.get_by_telegram_id(session, user_id)
    
    if not teacher:
        await callback_query.answer("You are not registered as a teacher.")
        return
    
    # Update submission
    try:
        # Update local database
        submission = await session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            await callback_query.answer("Submission not found.")
            return
        
        submission.status = "completed"
        submission.score = score
        submission.feedback = feedback
        submission.teacher_id = teacher.id
        await session.commit()
        
        # Update Django API
        response = await update_submission_score(submission_id, score, feedback, teacher.id)
        
        if not response.get("success"):
            logger.error(f"Error updating submission in API: {response.get('error')}")
            await callback_query.message.reply("Error updating submission in API. The submission was saved locally but may not be reflected in Django.")
        
        # Notify student
        student = await submission.get_student
        if student and student.telegram_id:
            try:
                await callback_query.bot.send_message(
                    student.telegram_id,
                    f"Your {submission.section.capitalize()} submission has been reviewed.\n\n"
                    f"Score: {score}/100\n\n"
                    f"Feedback: {feedback or 'No feedback provided'}"
                )
            except TelegramBadRequest:
                logger.warning(f"Could not send notification to student {student.telegram_id}")
        
        # Notify student via API
        if student:
            await notify_student(student.django_id, score, feedback, submission.section)
        
        # Update original message
        try:
            original_text = callback_query.message.text.split("\n\n✏️ Status:")[0]
            new_text = (
                f"{original_text}\n\n"
                f"✅ Status: Completed\n"
                f"Teacher: {teacher.full_name}\n"
                f"Score: {score}/100\n"
                f"Feedback: {feedback or 'No feedback provided'}"
            )
            await callback_query.message.edit_text(new_text)
        except TelegramBadRequest:
            # Message might be too old to edit, ignore
            pass
        
        # Clear state and send confirmation
        await state.clear()
        await callback_query.message.reply(
            "Submission successfully scored and feedback sent to student.",
            reply_markup=get_teacher_main_menu()
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error confirming score: {e}")
        await callback_query.answer(f"Error: {str(e)}")
        await state.clear()

@router.callback_query(F.data == "cancel")
async def process_cancel(callback_query: CallbackQuery, state: FSMContext):
    """Handle cancel button"""
    # Clear state
    await state.clear()
    
    await callback_query.message.reply(
        "Action cancelled.",
        reply_markup=get_teacher_main_menu()
    )
    await callback_query.answer()
