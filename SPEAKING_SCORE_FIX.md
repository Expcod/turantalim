# Speaking Test Score Fix

## Problem Description
The user reported that when checking a speaking test, the score returned was 27, but the API response showed `"percentage": 0` instead of the actual score.

## Root Cause Analysis
The issue was in the score calculation logic for speaking and writing tests in multilevel exams:

1. **Score Range Mismatch**: The `process_test_response` function always returns scores between 0-100, but multilevel speaking and writing tests should use scores between 0-75.

2. **Score Conversion Missing**: The speaking and writing test processing was not converting the 0-100 scores to 0-75 scores for multilevel exams.

## Solution Implemented

### 1. Fixed Speaking Test Score Conversion
**File**: `apps/multilevel/speaking_views.py`

Added score conversion logic for multilevel speaking tests:
```python
# Convert score from 0-100 to 0-75 for multilevel speaking tests
original_score = final_response.get("score", 0)
final_response["score"] = round((original_score / 100) * 75)
```

### 2. Fixed Writing Test Score Conversion
**File**: `apps/multilevel/writing_views.py`

Added similar score conversion logic for multilevel writing tests:
```python
# Convert score from 0-100 to 0-75 for multilevel writing tests
original_score = final_response.get("score", 0)
final_response["score"] = round((original_score / 100) * 75)
```

### 3. Fixed Score Saving Logic
**Files**: `apps/multilevel/speaking_views.py` and `apps/multilevel/writing_views.py`

Changed the condition for saving scores from:
```python
if total_questions == answered_questions and total_questions > 0:
```

To:
```python
if total_score > 0 and len(responses) > 0:
```

This ensures that scores are saved even if not all questions are answered, which handles cases where some questions might be skipped or failed to process.

## How It Works

1. **Score Calculation**: The `process_test_response` function calculates scores between 0-100 using OpenAI GPT-4.

2. **Score Conversion**: For multilevel exams, the speaking and writing test processing now converts these scores to the 0-75 range by applying the formula: `(original_score / 100) * 75`.

3. **Database Storage**: The converted score (0-75) is stored in the `TestResult.score` field.

4. **API Response**: The `TestResultDetailSerializer.get_percentage()` method correctly returns the stored score for speaking and writing tests.

## Expected Result
After this fix, when a speaking test returns a score of 27 (out of 75), the API response should show:
```json
{
  "id": 195,
  "section": "Turan Talim CEFR 1. Sınav Konuşma Bölümü",
  "language": "TR",
  "status": "completed",
  "start_time": "2025-08-23T22:45:39.846222+05:00",
  "end_time": "2025-08-23T22:59:39.846232+05:00",
  "total_questions": 8,
  "correct_answers": 0,
  "incorrect_answers": 8,
  "percentage": 27,  // Now shows the actual score instead of 0
  "level": "Below B1"
}
```

## Testing
To test the fix:
1. Run a speaking test for a multilevel exam
2. Check the API response at `/api/multilevel/test-result/{test_result_id}/`
3. Verify that the `percentage` field shows the correct score (0-75) instead of 0

## Files Modified
- `apps/multilevel/speaking_views.py` - Added score conversion and fixed score saving logic for speaking tests
- `apps/multilevel/writing_views.py` - Added score conversion and fixed score saving logic for writing tests
