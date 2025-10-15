# 🚀 Production Deployment Guide
## Turantalim API & Admin Dashboard

---

## 📋 Overview

**Domain:** `https://api.turantalim.uz`

**Services:**
- Backend API: `https://api.turantalim.uz/` (Django + Gunicorn)
- Admin Dashboard: `https://api.turantalim.uz/admin-dashboard/`
- Media Files: `https://api.turantalim.uz/media/`
- Static Files: `https://api.turantalim.uz/static/`

---

## 🔧 Prerequisites

```bash
# Ubuntu/Debian server
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql postgresql-contrib git supervisor
```

---

## 📦 Step 1: Setup Project

### 1.1 Clone Repository

```bash
cd /home/user
git clone https://github.com/your-repo/turantalim.git
cd turantalim
```

### 1.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 Setup Environment Variables

```bash
# Create .env file
nano .env
```

**Production .env:**
```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=api.turantalim.uz,www.turantalim.uz

# Database
DB_NAME=turantalim_db
DB_USER=turantalim_user
DB_PASSWORD=strong-password-here
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://turantalim.uz,https://www.turantalim.uz,https://api.turantalim.uz

# Media & Static
MEDIA_URL=/media/
STATIC_URL=/static/
MEDIA_ROOT=/home/user/turantalim/media
STATIC_ROOT=/home/user/turantalim/static

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis (if using cache)
REDIS_URL=redis://localhost:6379/0
```

---

## 🗄️ Step 2: Setup PostgreSQL

### 2.1 Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE turantalim_db;
CREATE USER turantalim_user WITH PASSWORD 'strong-password-here';
ALTER ROLE turantalim_user SET client_encoding TO 'utf8';
ALTER ROLE turantalim_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE turantalim_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE turantalim_db TO turantalim_user;
\q
```

### 2.2 Update Django Settings

Edit `core/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'turantalim_db'),
        'USER': os.getenv('DB_USER', 'turantalim_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### 2.3 Run Migrations

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## 🌐 Step 3: Setup Nginx

### 3.1 Copy Configuration

```bash
sudo cp /home/user/turantalim/nginx/turantalim.conf /etc/nginx/sites-available/turantalim
sudo ln -s /etc/nginx/sites-available/turantalim /etc/nginx/sites-enabled/
```

### 3.2 Test Configuration

```bash
sudo nginx -t
```

### 3.3 Remove Default Site (if exists)

```bash
sudo rm /etc/nginx/sites-enabled/default
```

---

## 🔐 Step 4: Setup SSL Certificate (Let's Encrypt)

### 4.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 4.2 Obtain Certificate

**IMPORTANT:** Before running this, make sure:
1. Domain `api.turantalim.uz` points to your server IP
2. Port 80 and 443 are open in firewall

```bash
sudo certbot --nginx -d api.turantalim.uz
```

Follow the prompts:
- Enter email address
- Agree to terms
- Choose to redirect HTTP to HTTPS

### 4.3 Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

### 4.4 Setup Auto-Renewal Cron Job

```bash
sudo crontab -e
```

Add this line:
```
0 3 * * * /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 🚀 Step 5: Setup Gunicorn

### 5.1 Install Gunicorn

```bash
source /home/user/turantalim/venv/bin/activate
pip install gunicorn
```

### 5.2 Create Gunicorn Configuration

```bash
nano /home/user/turantalim/gunicorn_config.py
```

```python
# Gunicorn configuration file
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 300
keepalive = 5

# Logging
accesslog = "/home/user/turantalim/logs/gunicorn_access.log"
errorlog = "/home/user/turantalim/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "turantalim"

# Server mechanics
daemon = False
pidfile = "/home/user/turantalim/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

### 5.3 Create Log Directory

```bash
mkdir -p /home/user/turantalim/logs
```

### 5.4 Test Gunicorn

```bash
cd /home/user/turantalim
source venv/bin/activate
gunicorn core.wsgi:application -c gunicorn_config.py
```

Press `Ctrl+C` to stop.

---

## 🔄 Step 6: Setup Supervisor (Process Manager)

### 6.1 Create Supervisor Configuration

```bash
sudo nano /etc/supervisor/conf.d/turantalim.conf
```

```ini
[program:turantalim]
command=/home/user/turantalim/venv/bin/gunicorn core.wsgi:application -c /home/user/turantalim/gunicorn_config.py
directory=/home/user/turantalim
user=user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/user/turantalim/logs/supervisor.log
environment=PATH="/home/user/turantalim/venv/bin"

[program:turantalim_celery]
command=/home/user/turantalim/venv/bin/celery -A core worker -l info
directory=/home/user/turantalim
user=user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/user/turantalim/logs/celery.log
environment=PATH="/home/user/turantalim/venv/bin"
```

### 6.2 Update Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start turantalim
```

### 6.3 Check Status

```bash
sudo supervisorctl status
```

---

## 🔥 Step 7: Setup Firewall

### 7.1 Configure UFW

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

---

## 📊 Step 8: Restart Services

```bash
# Restart Nginx
sudo systemctl restart nginx

# Restart Supervisor
sudo supervisorctl restart turantalim

# Check logs
sudo tail -f /home/user/turantalim/logs/gunicorn_error.log
```

---

## ✅ Step 9: Verify Deployment

### 9.1 Check API

```bash
curl https://api.turantalim.uz/
```

### 9.2 Check Admin Dashboard

Open browser: `https://api.turantalim.uz/admin-dashboard/`

### 9.3 Check Django Admin

Open browser: `https://api.turantalim.uz/admin/`

### 9.4 Test File Upload

Use Postman or curl to test writing/speaking submission.

---

## 🔧 Maintenance Commands

### Update Code

```bash
cd /home/user/turantalim
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart turantalim
```

### View Logs

```bash
# Nginx logs
sudo tail -f /var/log/nginx/turantalim_access.log
sudo tail -f /var/log/nginx/turantalim_error.log

# Gunicorn logs
tail -f /home/user/turantalim/logs/gunicorn_access.log
tail -f /home/user/turantalim/logs/gunicorn_error.log

# Supervisor logs
tail -f /home/user/turantalim/logs/supervisor.log
```

### Restart Services

```bash
# Restart all
sudo supervisorctl restart all
sudo systemctl restart nginx

# Restart specific service
sudo supervisorctl restart turantalim
```

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump turantalim_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo -u postgres psql turantalim_db < backup_20251008_120000.sql
```

---

## 🐛 Troubleshooting

### Issue 1: 502 Bad Gateway

**Check:**
```bash
# Is Gunicorn running?
sudo supervisorctl status turantalim

# Check logs
tail -f /home/user/turantalim/logs/gunicorn_error.log

# Restart
sudo supervisorctl restart turantalim
```

### Issue 2: Permission Denied (Media/Static)

**Fix:**
```bash
sudo chown -R user:user /home/user/turantalim/media
sudo chown -R user:user /home/user/turantalim/static
sudo chmod -R 755 /home/user/turantalim/media
sudo chmod -R 755 /home/user/turantalim/static
```

### Issue 3: Database Connection Error

**Check:**
```bash
# Is PostgreSQL running?
sudo systemctl status postgresql

# Can Django connect?
python manage.py dbshell
```

### Issue 4: SSL Certificate Error

**Check:**
```bash
# Certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Reload Nginx
sudo systemctl reload nginx
```

### Issue 5: Static Files Not Loading

**Fix:**
```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

---

## 📈 Performance Optimization

### 1. Enable Gzip Compression

Add to nginx config:
```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
```

### 2. Setup Redis Cache

```bash
sudo apt install redis-server
sudo systemctl enable redis-server
```

Update Django settings:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## 🔒 Security Checklist

- [ ] Change Django `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Use strong database password
- [ ] Enable firewall (UFW)
- [ ] Setup SSL certificate
- [ ] Restrict admin access
- [ ] Regular security updates
- [ ] Setup fail2ban
- [ ] Monitor logs regularly
- [ ] Backup database regularly

### Setup Fail2Ban

```bash
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📞 Monitoring & Alerts

### Setup Email Alerts

```bash
# Install sendmail
sudo apt install sendmail

# Configure in Django settings
ADMINS = [('Admin', 'admin@turantalim.uz')]
SERVER_EMAIL = 'server@turantalim.uz'
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Setup automatic alerts
crontab -e
```

Add:
```
0 */6 * * * /usr/bin/df -h | /usr/bin/mail -s "Disk Space Report" admin@turantalim.uz
```

---

## 🎯 Production URLs

After deployment, your URLs will be:

| Service | URL |
|---------|-----|
| API Base | `https://api.turantalim.uz/` |
| Admin Dashboard | `https://api.turantalim.uz/admin-dashboard/` |
| Django Admin | `https://api.turantalim.uz/admin/` |
| API Docs (Swagger) | `https://api.turantalim.uz/swagger/` |
| Media Files | `https://api.turantalim.uz/media/` |
| Writing Submit | `https://api.turantalim.uz/multilevel/testcheck/writing/` |
| Speaking Submit | `https://api.turantalim.uz/multilevel/testcheck/speaking/` |

---

## 📝 Update API Documentation

Update all documentation files with production URL:

```bash
# Update base URL in documentation
find . -name "*.md" -type f -exec sed -i 's|http://localhost:8000|https://api.turantalim.uz|g' {} +
```

---

**Last Updated:** October 8, 2025  
**Version:** 1.0.0  
**Server:** Ubuntu 22.04 LTS
