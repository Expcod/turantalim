#!/bin/bash
# Turantalim Production Deployment Script

set -e  # Exit on error

echo "🚀 Starting Turantalim Deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/user/turantalim"
VENV_DIR="$PROJECT_DIR/venv"

# Check if running as correct user
if [ "$USER" != "user" ]; then
    echo -e "${RED}❌ This script must be run as 'user'${NC}"
    exit 1
fi

# Navigate to project directory
cd $PROJECT_DIR

echo -e "${GREEN}✓${NC} Changed to project directory: $PROJECT_DIR"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source $VENV_DIR/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
else
    echo -e "${RED}❌ Virtual environment not found at $VENV_DIR${NC}"
    exit 1
fi

# Pull latest code
echo -e "${YELLOW}→${NC} Pulling latest code from Git..."
git pull origin main
echo -e "${GREEN}✓${NC} Code updated"

# Install/Update dependencies
echo -e "${YELLOW}→${NC} Installing dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Dependencies installed"

# Run database migrations
echo -e "${YELLOW}→${NC} Running database migrations..."
python manage.py migrate --noinput
echo -e "${GREEN}✓${NC} Migrations completed"

# Collect static files
echo -e "${YELLOW}→${NC} Collecting static files..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✓${NC} Static files collected"

# Clear cache (if using Redis)
if command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}→${NC} Clearing Redis cache..."
    redis-cli FLUSHDB
    echo -e "${GREEN}✓${NC} Cache cleared"
fi

# Restart services
echo -e "${YELLOW}→${NC} Restarting services..."

# Restart Gunicorn via Supervisor
sudo supervisorctl restart turantalim
echo -e "${GREEN}✓${NC} Gunicorn restarted"

# Reload Nginx
sudo systemctl reload nginx
echo -e "${GREEN}✓${NC} Nginx reloaded"

# Check service status
echo -e "${YELLOW}→${NC} Checking service status..."
sleep 2

if sudo supervisorctl status turantalim | grep -q "RUNNING"; then
    echo -e "${GREEN}✓${NC} Gunicorn is running"
else
    echo -e "${RED}❌ Gunicorn is not running${NC}"
    sudo supervisorctl tail turantalim
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓${NC} Nginx is running"
else
    echo -e "${RED}❌ Nginx is not running${NC}"
    sudo systemctl status nginx
    exit 1
fi

# Show logs
echo -e "\n${YELLOW}📋 Recent logs:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
sudo tail -n 20 $PROJECT_DIR/logs/gunicorn_error.log

echo -e "\n${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "🌐 API: https://api.turantalim.uz/"
echo -e "🔧 Admin Dashboard: https://api.turantalim.uz/admin-dashboard/"
echo -e "⚙️  Django Admin: https://api.turantalim.uz/admin/"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
