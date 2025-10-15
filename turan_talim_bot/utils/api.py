import aiohttp
import logging
import json
from typing import Optional, Dict, List, Any, Union

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DjangoAPIClient:
    """Client for communicating with Django API"""
    
    def __init__(self):
        self.base_url = Config.DJANGO_API_URL
        self.api_key = Config.DJANGO_API_KEY
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to Django API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data if data else None
                ) as response:
                    response_text = await response.text()
                    
                    try:
                        response_json = json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON from response: {response_text}")
                        return {"success": False, "error": "Invalid JSON response"}
                    
                    if response.status >= 400:
                        logger.error(f"API error: {response.status} - {response_json}")
                        return {"success": False, "error": response_json, "status": response.status}
                    
                    return {"success": True, "data": response_json}
        except aiohttp.ClientError as e:
            logger.error(f"API request error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pending_submissions(self) -> Dict:
        """Get all pending submissions from Django"""
        return await self._make_request("GET", "/api/multilevel/submissions/pending/")
    
    async def get_submission_detail(self, submission_id: int) -> Dict:
        """Get details for a specific submission"""
        return await self._make_request("GET", f"/api/multilevel/submissions/{submission_id}/")
    
    async def update_submission_status(self, submission_id: int, data: Dict) -> Dict:
        """Update submission status, score, feedback, etc."""
        return await self._make_request("PATCH", f"/api/multilevel/submissions/{submission_id}/", data)
    
    async def send_notification_to_student(self, user_id: int, message: str) -> Dict:
        """Send notification to a specific student via Django API"""
        return await self._make_request("POST", f"/api/notifications/", {
            "user_id": user_id,
            "message": message,
            "type": "exam_result"
        })

# Helper functions for common API operations
async def get_pending_submissions():
    """Get all pending writing and speaking submissions"""
    client = DjangoAPIClient()
    return await client.get_pending_submissions()

async def update_submission_status(submission_id: int, status: str, teacher_id: Optional[int] = None):
    """Update submission status (checking, completed)"""
    client = DjangoAPIClient()
    data = {"status": status}
    if teacher_id:
        data["teacher_id"] = teacher_id
    return await client.update_submission_status(submission_id, data)

async def update_submission_score(submission_id: int, score: int, feedback: str, teacher_id: int):
    """Update submission with score and feedback"""
    client = DjangoAPIClient()
    data = {
        "status": "completed",
        "score": score,
        "feedback": feedback,
        "teacher_id": teacher_id
    }
    return await client.update_submission_status(submission_id, data)

async def notify_student(user_id: int, score: int, feedback: str, section: str):
    """Send notification to student about their score"""
    client = DjangoAPIClient()
    message = f"Your {section.capitalize()} submission has been reviewed.\n\nScore: {score}/100\n\nFeedback: {feedback}"
    return await client.send_notification_to_student(user_id, message)
