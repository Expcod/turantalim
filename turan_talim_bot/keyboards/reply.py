from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_teacher_main_menu() -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard for teacher
    
    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    keyboard = [
        [KeyboardButton(text="📋 Pending Submissions")],
        [KeyboardButton(text="📊 My Statistics")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Choose an option"
    )

def get_admin_menu() -> ReplyKeyboardMarkup:
    """
    Create admin menu keyboard
    
    Returns:
        ReplyKeyboardMarkup with admin menu buttons
    """
    keyboard = [
        [KeyboardButton(text="📢 Broadcast Message")],
        [KeyboardButton(text="📊 Statistics")],
        [KeyboardButton(text="⬅️ Back")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Choose an admin option"
    )

def get_student_menu() -> ReplyKeyboardMarkup:
    """
    Create menu keyboard for student
    
    Returns:
        ReplyKeyboardMarkup with student menu buttons
    """
    keyboard = [
        [KeyboardButton(text="🔍 My Results")],
        [KeyboardButton(text="📞 Contact Support")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Choose an option"
    )

def get_back_button() -> ReplyKeyboardMarkup:
    """
    Create keyboard with back button
    
    Returns:
        ReplyKeyboardMarkup with back button
    """
    keyboard = [[KeyboardButton(text="⬅️ Back")]]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def get_score_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard with predefined score options
    
    Returns:
        ReplyKeyboardMarkup with score buttons
    """
    keyboard = [
        [KeyboardButton(text="100"), KeyboardButton(text="90"), KeyboardButton(text="80")],
        [KeyboardButton(text="70"), KeyboardButton(text="60"), KeyboardButton(text="50")],
        [KeyboardButton(text="40"), KeyboardButton(text="30"), KeyboardButton(text="20")],
        [KeyboardButton(text="❌ Cancel")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Enter score (0-100)"
    )

# Function to remove keyboard
def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Remove reply keyboard
    
    Returns:
        ReplyKeyboardRemove instance
    """
    return ReplyKeyboardRemove()
