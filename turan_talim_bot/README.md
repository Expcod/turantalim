# TuranTalim Bot

A Telegram bot for TuranTalim educational platform that allows teachers to review and score writing and speaking submissions from students taking Turkish language exams.

## Features

- Receive writing and speaking submissions from Django backend
- Store submissions in PostgreSQL database
- Send submissions to teachers for review
- Allow teachers to score submissions and provide feedback
- Notify students when their submissions are reviewed
- Support both webhook and polling modes

## Project Structure

```
turan_talim_bot/
│
├── bot.py                 # Main entry point
├── config.py              # Configuration and environment variables
├── database.py            # Database models and connection
├── requirements.txt       # Dependencies
│
├── handlers/              # Message handlers
│   ├── __init__.py
│   ├── teacher.py         # Teacher-specific handlers
│   └── student.py         # Student-specific handlers
│
├── keyboards/             # Telegram keyboard layouts
│   ├── __init__.py
│   ├── inline.py          # Inline keyboards
│   └── reply.py           # Reply keyboards
│
└── utils/                 # Utility functions
    ├── __init__.py
    ├── api.py             # Django API integration
    ├── logger.py          # Logging configuration
    └── states.py          # FSM states
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Django backend with REST API
- Telegram Bot Token

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/turan_talim_bot.git
cd turan_talim_bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-domain.com/telegram-webhook/
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443
DJANGO_API_URL=https://your-django-backend.com/api
DJANGO_API_KEY=your_django_api_key
ADMIN_ID=your_telegram_id
TEACHER_GROUP_ID=telegram_group_id_for_teachers
DATABASE_URL=postgresql+asyncpg://username:password@localhost/turan_talim
```

### Setting up Webhook

For production, use webhook mode for better performance:

1. Obtain an SSL certificate for your domain
2. Configure your web server (Nginx, Apache) to forward requests to the bot
3. Run the bot in webhook mode:
```bash
python bot.py
```

#### Using ngrok for local testing:

1. Download and install [ngrok](https://ngrok.com/)
2. Start ngrok tunnel to your local port:
```bash
ngrok http 8443
```
3. Update the `WEBHOOK_URL` in `.env` with the ngrok URL
4. Run the bot:
```bash
python bot.py
```

### Running in Polling Mode (Development)

For development, you can run the bot in polling mode:

```bash
python bot.py poll
```

## Connecting Django Backend to Bot

### API Endpoints

The bot expects the following API endpoints on the Django backend:

- `GET /api/multilevel/submissions/pending/` - Get pending submissions
- `GET /api/multilevel/submissions/{id}/` - Get submission details
- `PATCH /api/multilevel/submissions/{id}/` - Update submission status/score
- `POST /api/notifications/` - Send notification to student

### Adding API Endpoints to Django

1. Create a new API endpoint for pending submissions in your Django views:

```python
@api_view(['GET'])
def pending_submissions(request):
    # Get all writing and speaking submissions pending review
    pending_results = TestResult.objects.filter(
        section__type__in=['writing', 'speaking'],
        status='completed',
        score=0
    ).select_related('user_test__user')
    
    # Format data for the bot
    submissions = []
    for result in pending_results:
        submissions.append({
            'id': result.id,
            'section': result.section.type,
            'student_name': result.user_test.user.get_full_name(),
            'student_id': result.user_test.user.id,
            'created_at': result.created_at.isoformat()
        })
    
    return Response({'submissions': submissions})
```

2. Add URL patterns in your Django `urls.py`:

```python
urlpatterns = [
    # ... other URLs
    path('api/multilevel/submissions/pending/', views.pending_submissions),
    path('api/multilevel/submissions/<int:pk>/', views.submission_detail),
    path('api/notifications/', views.send_notification),
]
```

## Teacher Workflow

1. Teacher opens the bot and views pending submissions
2. Teacher selects a submission to review
3. Teacher marks the submission as "Checking" while they review
4. Teacher adds a score (0-100) and feedback
5. Teacher submits the review
6. The student is notified of their score

## Troubleshooting

- Check logs in the `logs` directory for errors
- Ensure environment variables are correctly set
- Verify the connection to the Django API using the debug endpoints
- Make sure the PostgreSQL database is running and accessible

## License

This project is licensed under the MIT License - see the LICENSE file for details.
