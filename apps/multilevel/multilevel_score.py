"""
Multilevel test scoring system for Listening and Reading tests.
This module provides scoring functions based on the number of correct answers.
"""

# Listening test scoring table
LISTENING_SCORES = {
    1: 23, 2: 26, 3: 28, 4: 30, 5: 33, 6: 34, 7: 36, 8: 38, 9: 39, 10: 41,
    11: 42, 12: 44, 13: 45, 14: 47, 15: 48, 16: 50, 17: 51, 18: 53, 19: 54,
    20: 55, 21: 57, 22: 58, 23: 60, 24: 61, 25: 63, 26: 65, 27: 66, 28: 68,
    29: 70, 30: 72, 31: 73, 32: 74, 33: 75, 34: 75, 35: 75
}

# Reading test scoring table
READING_SCORES = {
    1: 20, 2: 24, 3: 27, 4: 29, 5: 32, 6: 34, 7: 36, 8: 38, 9: 39, 10: 41,
    11: 42, 12: 44, 13: 45, 14: 46, 15: 48, 16: 49, 17: 51, 18: 52, 19: 54,
    20: 55, 21: 57, 22: 58, 23: 60, 24: 61, 25: 63, 26: 65, 27: 66, 28: 68,
    29: 70, 30: 71, 31: 73, 32: 74, 33: 75, 34: 75, 35: 75
}


def get_listening_score(correct_answers):
    """
    Get listening test score based on number of correct answers.
    
    Args:
        correct_answers (int): Number of correct answers (1-35)
    
    Returns:
        int: Score from 0-75
        
    Raises:
        ValueError: If correct_answers is not in valid range
    """
    if not isinstance(correct_answers, int):
        raise ValueError("correct_answers must be an integer")
    
    if correct_answers < 0:
        return 0
    elif correct_answers > 35:
        return 75  # Maximum score for more than 35 correct answers
    else:
        return LISTENING_SCORES.get(correct_answers, 0)


def get_reading_score(correct_answers):
    """
    Get reading test score based on number of correct answers.
    
    Args:
        correct_answers (int): Number of correct answers (1-35)
    
    Returns:
        int: Score from 0-75
        
    Raises:
        ValueError: If correct_answers is not in valid range
    """
    if not isinstance(correct_answers, int):
        raise ValueError("correct_answers must be an integer")
    
    if correct_answers < 0:
        return 0
    elif correct_answers > 35:
        return 75  # Maximum score for more than 35 correct answers
    else:
        return READING_SCORES.get(correct_answers, 0)


def get_test_score(test_type, correct_answers):
    """
    Get test score based on test type and number of correct answers.
    
    Args:
        test_type (str): Type of test ('listening' or 'reading')
        correct_answers (int): Number of correct answers
    
    Returns:
        int: Score from 0-75
        
    Raises:
        ValueError: If test_type is not valid or correct_answers is invalid
    """
    if test_type.lower() == 'listening':
        return get_listening_score(correct_answers)
    elif test_type.lower() == 'reading':
        return get_reading_score(correct_answers)
    else:
        raise ValueError("test_type must be 'listening' or 'reading'")


def validate_test_level(level):
    """
    Validate if the test level is supported for multilevel scoring.
    
    Args:
        level (str): Test level to validate
    
    Returns:
        bool: True if level is supported, False otherwise
    """
    supported_levels = ['multilevel', 'a1', 'a2', 'b1', 'b2', 'c1']
    return level.lower() in supported_levels


def get_score_details(test_type, correct_answers, total_questions):
    """
    Get detailed score information including percentage and level.
    
    Args:
        test_type (str): Type of test ('listening' or 'reading')
        correct_answers (int): Number of correct answers
        total_questions (int): Total number of questions
    
    Returns:
        dict: Dictionary containing score details
    """
    if total_questions <= 0:
        return {
            'score': 0,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'percentage': 0,
            'level': 'Below A1'
        }
    
    # Get score from scoring table
    score = get_test_score(test_type, correct_answers)
    
    # Calculate percentage
    percentage = (correct_answers / total_questions) * 100
    
    # Determine level based on score
    level = get_level_from_score(score)
    
    return {
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'percentage': round(percentage, 2),
        'level': level
    }


def get_level_from_score(score):
    """
    Determine CEFR level based on average score (0-75).
    
    Args:
        score (int): Average test score (0-75)
    
    Returns:
        str: CEFR level
    """
    if score >= 65:
        return "C1"
    elif score >= 51:
        return "B2"
    elif score >= 38:
        return "B1"
    else:
        return "Below B1"


def get_all_scores():
    """
    Get all possible scores for both listening and reading tests.
    
    Returns:
        dict: Dictionary with all scores for both test types
    """
    return {
        'listening': LISTENING_SCORES,
        'reading': READING_SCORES
    }


def get_score_range(test_type, min_correct=1, max_correct=35):
    """
    Get score range for a specific test type.
    
    Args:
        test_type (str): Type of test ('listening' or 'reading')
        min_correct (int): Minimum number of correct answers
        max_correct (int): Maximum number of correct answers
    
    Returns:
        dict: Dictionary with score range information
    """
    if test_type.lower() == 'listening':
        scores = {k: v for k, v in LISTENING_SCORES.items() 
                 if min_correct <= k <= max_correct}
    elif test_type.lower() == 'reading':
        scores = {k: v for k, v in READING_SCORES.items() 
                 if min_correct <= k <= max_correct}
    else:
        raise ValueError("test_type must be 'listening' or 'reading'")
    
    return {
        'test_type': test_type,
        'min_correct': min_correct,
        'max_correct': max_correct,
        'min_score': min(scores.values()) if scores else 0,
        'max_score': max(scores.values()) if scores else 0,
        'scores': scores
    }


def count_words(text):
    """
    Count words in text.
    
    Args:
        text (str): Text to count words in
    
    Returns:
        int: Number of words
    """
    if not text:
        return 0
    # Remove extra whitespace and split by spaces
    words = text.strip().split()
    return len(words)


def get_writing_score_details(text, question_part=1):
    """
    Get writing score details based on text length and content.
    
    Args:
        text (str): The written text
        question_part (int): Part of the question (1 or 2)
    
    Returns:
        dict: Dictionary containing score details
    """
    word_count = count_words(text)
    
    if question_part == 1:
        # 1-bo'lim: 25 ball, maqsad 150 so'z, minimal 70 so'z
        target_words = 150
        min_words = 70
        max_score = 25
        
        if word_count < min_words:
            return {
                'score': 0,
                'word_count': word_count,
                'min_required': min_words,
                'target_words': target_words,
                'reason': f"Matn juda qisqa. Minimal {min_words} so'z kerak, {word_count} so'z yozilgan."
            }
    else:
        # 2-bo'lim: 50 ball, maqsad 250 so'z, minimal 110 so'z
        target_words = 250
        min_words = 110
        max_score = 50
        
        if word_count < min_words:
            return {
                'score': 0,
                'word_count': word_count,
                'min_required': min_words,
                'target_words': target_words,
                'reason': f"Matn juda qisqa. Minimal {min_words} so'z kerak, {word_count} so'z yozilgan."
            }
    
    return {
        'score': None,  # Will be calculated by ChatGPT
        'word_count': word_count,
        'min_required': min_words,
        'target_words': target_words,
        'max_score': max_score,
        'word_count_ok': word_count >= min_words
    }


def get_writing_rubric(question_part=1):
    """
    Get writing rubric based on question part.
    
    Args:
        question_part (int): Part of the question (1 or 2)
    
    Returns:
        str: Detailed rubric for evaluation
    """
    if question_part == 1:
        return """
BAHOLASH MEZONLARI (1-bo'lim - 25 ball):

1. MAZMUN MOSLIGI VA TO'G'RILIGI (12 ball):
   - Savolga to'liq javob berish
   - Ma'lumot xatolari (-2 ball har bir xato uchun)
   - Mavzudan chetga chiqish ≥30% bo'lsa (-2 ball)

2. MANTIQIY IZCHILLIK VA MULOHAZA YURITISH (5 ball):
   - Fikrlar mantiqli asos yoki misol bilan tasdiqlanishi
   - Asoslanmagan har bir asosiy fikr uchun (-1 ball, maksimal -3)

3. MATN TUZILISHI VA TASHKIL ETILISHI (3 ball):
   - Paragraflar to'g'ri tuzilgan
   - Matn tuzilishi mantiqli

4. TIL ISHLATISH VA IFODALASH (3 ball):
   - Grammatik to'g'rilik
   - Leksik boylik

5. YO'RIQNOMAGA RIOYA QILISH (2 ball):
   - Savol bo'limlarini javoblash
   - Talab qilingan shakl
   - Mavzudan chetga chiqish ≥30% bo'lsa (-2 ball)

JAMI: 25 ball (bazaviy)
"""
    else:
        return """
BAHOLASH MEZONLARI (2-bo'lim - 50 ball):

1. MAZMUN MOSLIGI VA TO'G'RILIGI (24 ball):
   - Savolga to'liq javob berish
   - Ma'lumot xatolari (-2 ball har bir xato uchun)
   - Mavzudan chetga chiqish ≥30% bo'lsa (-2 ball)

2. MANTIQIY IZCHILLIK VA MULOHAZA YURITISH (10 ball):
   - Fikrlar mantiqli asos yoki misol bilan tasdiqlanishi
   - Asoslanmagan har bir asosiy fikr uchun (-1 ball, maksimal -3)

3. MATN TUZILISHI VA TASHKIL ETILISHI (6 ball):
   - Paragraflar to'g'ri tuzilgan
   - Matn tuzilishi mantiqli

4. TIL ISHLATISH VA IFODALASH (6 ball):
   - Grammatik to'g'rilik
   - Leksik boylik

5. YO'RIQNOMAGA RIOYA QILISH (4 ball):
   - Savol bo'limlarini javoblash
   - Talab qilingan shakl
   - Mavzudan chetga chiqish ≥30% bo'lsa (-2 ball)

JAMI: 50 ball (bazaviy)
"""


def get_writing_prompt(question_text, constraints, user_answer, question_part=1):
    """
    Generate comprehensive writing evaluation prompt.
    
    Args:
        question_text (str): The question text
        constraints (str): Question constraints
        user_answer (str): User's written answer
        question_part (int): Part of the question (1 or 2)
    
    Returns:
        str: Complete evaluation prompt
    """
    word_count = count_words(user_answer)
    rubric = get_writing_rubric(question_part)
    
    prompt = f"""
Siz professional writing baholovchisiz. Quyidagi matnni aniq va adolatli baholang.

SAVOL: {question_text}

CHEKLOVLAR/SHARTLAR: {constraints if constraints else "Cheklovlar yo'q"}

FOYDALANUVCHI JAVOBI: {user_answer}

SO'ZLAR SONI: {word_count} so'z

{rubric}

BAHOLASH TALABLARI:
1. Har bir mezon uchun alohida ball bering
2. Ayirishlar (-2, -1 ball) qo'llang
3. Mavzudan chetga chiqish ≥30% bo'lsa tegishli ayirishlar qo'llang
4. Ma'lumot xatolari uchun -2 ball har bir xato
5. Asoslanmagan fikrlar uchun -1 ball (maksimal -3)

FAQAT JSON FORMATDA JAVOB BERING:
{{
    "score": <0-{25 if question_part == 1 else 50}>,
    "content_relevance": <0-{12 if question_part == 1 else 24}>,
    "logical_coherence": <0-{5 if question_part == 1 else 10}>,
    "text_structure": <0-{3 if question_part == 1 else 6}>,
    "language_usage": <0-{3 if question_part == 1 else 6}>,
    "instruction_following": <0-{2 if question_part == 1 else 4}>,
    "deductions": {{
        "factual_errors": <soni>,
        "unsubstantiated_claims": <soni>,
        "off_topic_percentage": <foiz>
    }},
    "comment": "Batafsil tahlil va tavsiyalar"
}}
"""
    return prompt


def process_speaking_response(response_data):
    """
    Process and validate speaking test response from ChatGPT.
    
    Args:
        response_data (dict): Response data from ChatGPT
    
    Returns:
        dict: Processed and validated response
    """
    try:
        # Extract overall score
        overall_score = response_data.get('overall', 0)
        max_score = response_data.get('max', 75)
        
        # Validate score range
        if not isinstance(overall_score, (int, float)) or overall_score < 0 or overall_score > max_score:
            overall_score = 0
        
        # Extract criteria scores
        criteria = response_data.get('criteria', [])
        criteria_scores = {}
        
        for criterion in criteria:
            name = criterion.get('name', '')
            score = criterion.get('score', 0)
            max_criterion = criterion.get('max', 0)
            notes = criterion.get('notes', [])
            
            if name and isinstance(score, (int, float)) and score >= 0:
                criteria_scores[name] = {
                    'score': score,
                    'max': max_criterion,
                    'notes': notes
                }
        
        # Extract deductions
        deductions = response_data.get('deductions', {})
        
        # Extract improvements
        improvements = response_data.get('improvements', [])
        if not isinstance(improvements, list):
            improvements = []
        
        # Extract detailed comment
        detailed_comment = response_data.get('detailed_comment', '')
        
        return {
            'score': int(overall_score),
            'max_score': max_score,
            'criteria': criteria_scores,
            'deductions': deductions,
            'improvements': improvements,
            'detailed_comment': detailed_comment,
            'is_valid': True
        }
        
    except Exception as e:
        # Fallback to simple score if processing fails
        return {
            'score': 0,
            'max_score': 75,
            'criteria': {},
            'deductions': {},
            'improvements': [],
            'detailed_comment': f"Response processing error: {str(e)}",
            'is_valid': False
        }


def get_speaking_rubric():
    """
    Get speaking test rubric for multilevel scoring based on Uzbek language criteria.
    
    Returns:
        str: Detailed rubric for speaking evaluation
    """
    return """
BAHOLASH MEZONLARI (Speaking - 75 ball):

1. MAZMUN VA TO'G'RILIK (35 ball):
   - Savolga to'liq javob berish
   - Ma'lumot xatolari (-2 ball har bir xato uchun, maksimal -8 ball)
   - Mavzudan chetga chiqish ≥30% bo'lsa (-4 ball qo'shimcha)

2. MANTIQ (12 ball):
   - Sabab-oqibat aniqligi
   - Fikrlar mantiqli asos yoki misol bilan tasdiqlanishi
   - Asoslanmagan har bir asosiy fikr uchun (-1 ball, maksimal -3)
   - Yakun qismi to'liqligi

3. TUZILISH (8 ball):
   - Kirish aniqligi
   - Paragraflar to'g'ri tuzilgan
   - Yakun qismi umumlashtirilishi

4. TIL VA USLUB (8 ball):
   - Terminlar joyida ishlatilishi
   - Grammatik to'g'rilik
   - Kichik uslub xatolari (-1 ball)

5. RAVONLIK/VAQT (6 ball):
   - Tabiiy ravonlik
   - To'ldiruvchi so'zlar yoki sukut boshqaruvi (-1 yoki -2 ball)
   - Nutq oqimini buzmaslik

6. TALAFFUZ/TUSHUNARLILIK (4 ball):
   - Tushunarli daraja yuqori
   - To'g'ri talaffuz
   - Intonatsiya va urg'u

7. YO'RIQNOMA TALABLARIGA MOSLIK (2 ball):
   - Tartib va vaqtga rioya qilish
   - Talab qilingan shakl

JAMI: 75 ball
"""


def get_speaking_prompt(question_text, constraints, user_answer):
    """
    Generate comprehensive speaking evaluation prompt based on Uzbek language criteria.
    
    Args:
        question_text (str): The question text
        constraints (str): Question constraints
        user_answer (str): User's transcribed answer
    
    Returns:
        str: Complete evaluation prompt
    """
    word_count = count_words(user_answer)
    rubric = get_speaking_rubric()
    
    prompt = f"""
Siz professional speaking baholovchisiz. Quyidagi audio transkripsiyasini aniq va adolatli baholang.

SAVOL: {question_text}

CHEKLOVLAR/SHARTLAR: {constraints if constraints else "Cheklovlar yo'q"}

FOYDALANUVCHI JAVOBI (Transkripsiya): {user_answer}

SO'ZLAR SONI: {word_count} so'z

{rubric}

ANIQLIK QOIDALARI:
* Qisman ball: Har bir kichik mezon 0 dan to to'liq ballgacha qisman beriladi (yomon = 25%, o'rta = 50%, yaxshi = 75%, to'liq = 100%).
* Noto'g'ri ma'lumot uchun kesinti: Har bir aniq va muhim xato uchun –2 ball (maksimal –8 ball), bu MAZMUN VA TO'G'RILIK kichik mezonidan ayriladi.
* Mavzudan chetga chiqish: Javobning ≥30% mavzuga aloqasiz bo'lsa, "Savolga to'liq javob berish" kichik mezonidan –4 ball qo'shimcha olib tashlanadi.
* Dalilsiz da'vo: "Shunday" deb aytilib, asos keltirilmagan har bir asosiy fikr uchun MANTIQ mezonidan –1 ball (maksimal –3).
* To'ldiruvchi so'zlar / sukut boshqaruvi: Agar uzun va takroriy to'ldiruvchi so'zlar yoki sukut nutq oqimini buzsa, RAVONLIK bo'limidan –1 yoki –2 ball kesiladi.
* Betaraflik va xolislik: Baholovchi aksent, jins, ohang kabi mazmunga aloqasi bo'lmagan jihatlarni baholashga qo'shmaydi.

BAHOLASH TALABLARI:
1. Har bir mezon uchun alohida ball bering
2. Qisman ball berish (25%, 50%, 75%, 100%)
3. Ayirishlar qo'llang (-1, -2, -4 ball)
4. Mavzudan chetga chiqish ≥30% bo'lsa tegishli ayirishlar qo'llang
5. Ma'lumot xatolari uchun -2 ball har bir xato (maksimal -8)
6. Asoslanmagan fikrlar uchun -1 ball (maksimal -3)
7. To'ldiruvchi so'zlar uchun -1 yoki -2 ball

FAQAT JSON FORMATDA JAVOB BERING:
{{
    "overall": <0-75>,
    "max": 75,
    "criteria": [
        {{"name": "Mazmun va To'g'rilik", "score": <0-35>, "max": 35, "notes": ["<izohlar>"]}},
        {{"name": "Mantiq", "score": <0-12>, "max": 12, "notes": ["<izohlar>"]}},
        {{"name": "Tuzilish", "score": <0-8>, "max": 8, "notes": ["<izohlar>"]}},
        {{"name": "Til va Uslub", "score": <0-8>, "max": 8, "notes": ["<izohlar>"]}},
        {{"name": "Ravonlik/Vaqt", "score": <0-6>, "max": 6, "notes": ["<izohlar>"]}},
        {{"name": "Talaffuz/Tushunarlilik", "score": <0-4>, "max": 4, "notes": ["<izohlar>"]}},
        {{"name": "Yo'riqnoma Talablariga Moslik", "score": <0-2>, "max": 2, "notes": ["<izohlar>"]}}
    ],
    "deductions": {{
        "factual_errors": <soni>,
        "unsubstantiated_claims": <soni>,
        "off_topic_percentage": <foiz>,
        "filler_words": <soni>
    }},
    "improvements": [
        "<tavsiya 1>",
        "<tavsiya 2>",
        "<tavsiya 3>"
    ],
    "detailed_comment": "Batafsil tahlil va tavsiyalar"
}}
"""
    return prompt


def calculate_overall_test_result(user_test_id):
    """
    Calculate overall test result for a user test.
    
    Args:
        user_test_id (int): UserTest ID
    
    Returns:
        dict: Overall test result with scores and level
    """
    from .models import UserTest, TestResult, Section
    
    try:
        user_test = UserTest.objects.get(id=user_test_id)
        
        # Check if this is a multilevel exam
        is_multilevel = user_test.exam.level == 'multilevel'
        
        if is_multilevel:
            # For multilevel exams, check if all sections are completed
            total_sections = Section.objects.filter(exam=user_test.exam).count()
            completed_sections = TestResult.objects.filter(
                user_test=user_test,
                status='completed'
            ).count()
            
            # If not all sections are completed, return error
            if completed_sections < total_sections:
                return {
                    'error': f'Multilevel imtihon yakunlanmagan. {completed_sections}/{total_sections} bo\'lim tugatilgan.',
                    'user_test_id': user_test_id,
                    'completed_sections': completed_sections,
                    'total_sections': total_sections,
                    'is_multilevel': True
                }
        
        # Get all completed test results for this user test
        test_results = TestResult.objects.filter(
            user_test=user_test,
            status='completed'
        ).select_related('section')
        
        if not test_results.exists():
            return {
                'error': 'No completed test results found',
                'user_test_id': user_test_id
            }
        
        # Initialize section scores
        section_scores = {
            'listening': 0,
            'reading': 0,
            'writing': 0,
            'speaking': 0
        }
        
        total_score = 0
        completed_sections = 0
        
        # Calculate scores for each section
        for test_result in test_results:
            section_type = test_result.section.type
            if section_type in section_scores:
                section_scores[section_type] = test_result.score
                total_score += test_result.score
                completed_sections += 1
        
        # Calculate average score based on exam type
        if is_multilevel:
            # For multilevel: divide by 4 sections
            average_score = total_score / 4 if completed_sections == 4 else 0
            max_possible_score = 300  # 4 sections * 75 points each
        else:
            # For other levels: use the single section score
            average_score = total_score
            max_possible_score = 75  # Single section max score
        
        # Determine level based on average score
        level = get_level_from_score(average_score)
        
        return {
            'user_test_id': user_test_id,
            'user_id': user_test.user.id,
            'exam_name': user_test.exam.name,
            'exam_level': user_test.exam.level,
            'section_scores': {
                'listening': section_scores['listening'],
                'reading': section_scores['reading'],
                'writing': section_scores['writing'],
                'speaking': section_scores['speaking']
            },
            'total_score': total_score,
            'max_possible_score': max_possible_score,
            'average_score': round(average_score, 2),
            'level': level,
            'completed_sections': completed_sections,
            'total_sections': 4 if is_multilevel else 1,
            'is_complete': True,
            'is_multilevel': is_multilevel
        }
        
    except UserTest.DoesNotExist:
        return {
            'error': 'User test not found',
            'user_test_id': user_test_id
        }
    except Exception as e:
        return {
            'error': f'Error calculating test result: {str(e)}',
            'user_test_id': user_test_id
        }
