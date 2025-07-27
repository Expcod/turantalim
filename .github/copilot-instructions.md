# TuranTalim - AI Assistant Instructions

This is a Django-based learning management system (LMS) with multilevel testing capabilities. Here are the key patterns and conventions to be aware of:

## Project Structure

- **Apps Organization**:
  - `apps/multilevel/` - Core testing/exam functionality
  - `apps/users/` - User management 
  - `apps/payment/` - Payment processing (Payme integration)
  - `apps/main/` - General functionality
  - `apps/dashboard/` - Admin dashboard features

## Key Architectural Patterns

1. **Admin Interface**
   - Custom admin views in `apps/multilevel/admin_views.py`
   - Admin templates in `templates/admin/`
   - Uses Jazzmin for enhanced admin UI
   - URL namespace 'admin' for custom admin views

2. **API Architecture** 
   - REST framework with JWT authentication
   - API views use `@api_view` decorator
   - Swagger/OpenAPI documentation enabled
   - Standard response format with pagination

3. **Testing System**
   - Multi-level testing with different types (writing, speaking)
   - Test results and user progress tracking
   - Serializers handle test submission validation

## Development Workflow

1. **Environment Setup**
   - Uses python-environ for .env configuration
   - Requires redis for Celery background tasks
   - Development settings in `core/settings/develop.py`

2. **Templates & Frontend**
   - Templates use Tailwind CSS 
   - Alpine.js for interactive components
   - Lucide icons for UI elements
   - Templates extend from `templates/admin/base.html`

3. **API Development**
   - API endpoints documented with drf-spectacular
   - CORS enabled for all origins in development
   - JWT tokens with 7-day access, 30-day refresh

## Common Patterns

1. **View Decorators**
   - `@staff_member_required` for admin views
   - `@api_view` for API endpoints
   - `@permission_classes([IsAdminUser])` for admin APIs

2. **Model Conventions**
   - Language field for multilingual content
   - Price fields for exam/course costs
   - Duration fields for time limits

3. **Integration Points**
   - Payment gateway (Payme)
   - SMS notifications (Eskiz)
   - OpenAI integration
   - Telegram bot notifications

## Critical Files
- `core/settings/base.py` - Core configuration
- `core/urls.py` - Main URL routing
- `apps/multilevel/admin_views.py` - Admin panel views
- `templates/admin/base.html` - Base admin template

## Testing & Debugging
- Django test classes in each app's `tests.py`
- Development server: `python manage.py runserver`
- Celery worker: `celery -A core worker -l info`
