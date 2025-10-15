from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_submission_actions_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with submission action buttons
    
    Args:
        submission_id: ID of the submission
        
    Returns:
        InlineKeyboardMarkup with action buttons
    """
    builder = InlineKeyboardBuilder()
    
    # Add Mark as Checked button
    builder.add(
        InlineKeyboardButton(
            text="🟢 Mark as Checked",
            callback_data=f"mark_checked:{submission_id}"
        )
    )
    
    # Add Add Score button
    builder.add(
        InlineKeyboardButton(
            text="📝 Add Score", 
            callback_data=f"add_score:{submission_id}"
        )
    )
    
    # Adjust layout (1 button per row)
    builder.adjust(1)
    
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard with cancel button
    
    Returns:
        InlineKeyboardMarkup with cancel button
    """
    builder = InlineKeyboardBuilder()
    
    # Add Cancel button
    builder.add(
        InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()

def get_confirm_score_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with confirm and cancel buttons for score submission
    
    Args:
        submission_id: ID of the submission
        
    Returns:
        InlineKeyboardMarkup with confirm and cancel buttons
    """
    builder = InlineKeyboardBuilder()
    
    # Add Confirm button
    builder.add(
        InlineKeyboardButton(
            text="✅ Confirm",
            callback_data=f"confirm_score:{submission_id}"
        )
    )
    
    # Add Cancel button
    builder.add(
        InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="cancel"
        )
    )
    
    # Adjust layout (2 buttons per row)
    builder.adjust(2)
    
    return builder.as_markup()
