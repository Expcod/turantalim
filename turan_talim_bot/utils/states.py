from aiogram.fsm.state import State, StatesGroup

class TeacherState(StatesGroup):
    """States for teacher scoring process"""
    waiting_for_score = State()
    waiting_for_feedback = State()
    
class AdminState(StatesGroup):
    """States for admin operations"""
    waiting_for_broadcast_message = State()
    waiting_for_user_id = State()
    
class ScoreData:
    """Helper class to store temporary data during scoring process"""
    def __init__(self):
        self.submission_id = None
        self.score = None
        self.feedback = None
