# ⚡ Quick Setup Commands - Production

Bu fayl production serverga tez deploy qilish uchun barcha kerakli buyruqlarni o'z ichiga oladi.

---

## 🔧 Initial Server Setup (One Time)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql postgresql-contrib git supervisor redis-server

# 3. Setup PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE turantalim_db;"
sudo -u postgres psql -c "CREATE USER turantalim_user WITH PASSWORD 'your-strong-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE turantalim_db TO turantalim_user;"

# 4. Clone project
cd /home/user
git clone https://github.com/your-repo/turantalim.git
cd turantalim

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Setup environment
cp env.production.example .env
nano .env  # Edit with your values

# 7. Run migrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

# 8. Create directories
mkdir -p /home/user/turantalim/logs
mkdir -p /home/user/turantalim/media
mkdir -p /home/user/turantalim/static

# 9. Setup Nginx
sudo cp nginx/turantalim.conf /etc/nginx/sites-available/turantalim
sudo ln -s /etc/nginx/sites-available/turantalim /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 10. Setup SSL (Make sure DNS points to your server first!)
sudo certbot --nginx -d api.turantalim.uz

# 11. Setup Supervisor
sudo cp supervisor/turantalim.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start turantalim

# 12. Setup Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 13. Verify
curl https://api.turantalim.uz/
```

---

## 🚀 Deployment (Every Update)

```bash
# Quick deploy
cd /home/user/turantalim
./deploy.sh
```

**OR manually:**

```bash
cd /home/user/turantalim
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart turantalim
sudo systemctl reload nginx
```

---

## 🔍 Monitoring Commands

### Check Service Status
```bash
# All services
sudo supervisorctl status

# Nginx
sudo systemctl status nginx

# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server
```

### View Logs
```bash
# Gunicorn logs
tail -f /home/user/turantalim/logs/gunicorn_error.log
tail -f /home/user/turantalim/logs/gunicorn_access.log

# Nginx logs
sudo tail -f /var/log/nginx/turantalim_error.log
sudo tail -f /var/log/nginx/turantalim_access.log

# Supervisor logs
tail -f /home/user/turantalim/logs/supervisor.log
```

### Restart Services
```bash
# Restart Gunicorn
sudo supervisorctl restart turantalim

# Restart Nginx
sudo systemctl restart nginx

# Restart all
sudo supervisorctl restart all && sudo systemctl restart nginx
```

---

## 🗄️ Database Commands

### Backup
```bash
# Create backup
sudo -u postgres pg_dump turantalim_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Create backup with compression
sudo -u postgres pg_dump turantalim_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore
```bash
# Restore from backup
sudo -u postgres psql turantalim_db < backup_20251008_120000.sql

# Restore from compressed backup
gunzip -c backup_20251008_120000.sql.gz | sudo -u postgres psql turantalim_db
```

### Database Shell
```bash
# Django shell
cd /home/user/turantalim
source venv/bin/activate
python manage.py dbshell

# PostgreSQL directly
sudo -u postgres psql turantalim_db
```

---

## 🧹 Maintenance Commands

### Clear Cache
```bash
# Redis cache
redis-cli FLUSHDB

# Django cache
cd /home/user/turantalim
source venv/bin/activate
python manage.py clear_cache
```

### Clean Old Media Files
```bash
# Find files older than 30 days
find /home/user/turantalim/media -type f -mtime +30

# Delete files older than 30 days (be careful!)
find /home/user/turantalim/media -type f -mtime +30 -delete
```

### Disk Space
```bash
# Check disk usage
df -h

# Check directory size
du -sh /home/user/turantalim/media
du -sh /home/user/turantalim/logs
```

### Clean Logs
```bash
# Truncate old logs
sudo truncate -s 0 /var/log/nginx/turantalim_access.log
sudo truncate -s 0 /var/log/nginx/turantalim_error.log
truncate -s 0 /home/user/turantalim/logs/gunicorn_access.log
truncate -s 0 /home/user/turantalim/logs/gunicorn_error.log
```

---

## 🔐 SSL Certificate

### Renew Certificate
```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Check certificate
sudo certbot certificates
```

### Auto-Renewal Cron
```bash
# Edit crontab
sudo crontab -e

# Add this line
0 3 * * * /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 🐛 Troubleshooting

### 502 Bad Gateway
```bash
# Check if Gunicorn is running
sudo supervisorctl status turantalim

# View error logs
tail -f /home/user/turantalim/logs/gunicorn_error.log

# Restart
sudo supervisorctl restart turantalim
```

### Static Files Not Loading
```bash
# Recollect static files
cd /home/user/turantalim
source venv/bin/activate
python manage.py collectstatic --noinput

# Check permissions
ls -la /home/user/turantalim/static

# Restart Nginx
sudo systemctl restart nginx
```

### Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep turantalim

# Check connection
cd /home/user/turantalim
source venv/bin/activate
python manage.py dbshell
```

### Permission Issues
```bash
# Fix media directory permissions
sudo chown -R user:user /home/user/turantalim/media
sudo chmod -R 755 /home/user/turantalim/media

# Fix static directory permissions
sudo chown -R user:user /home/user/turantalim/static
sudo chmod -R 755 /home/user/turantalim/static

# Fix logs directory permissions
sudo chown -R user:user /home/user/turantalim/logs
sudo chmod -R 755 /home/user/turantalim/logs
```

---

## 📊 Performance Monitoring

### Check CPU & Memory
```bash
# System resources
htop

# Process specific
ps aux | grep gunicorn
ps aux | grep nginx

# Memory usage
free -h
```

### Check Open Connections
```bash
# Nginx connections
sudo netstat -tuln | grep :80
sudo netstat -tuln | grep :443

# Gunicorn connections
sudo netstat -tuln | grep :8000

# PostgreSQL connections
sudo -u postgres psql turantalim_db -c "SELECT COUNT(*) FROM pg_stat_activity;"
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 https://api.turantalim.uz/

# Test with authentication
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" https://api.turantalim.uz/multilevel/test-results/
```

---

## 🔄 Update System

### Update Django
```bash
cd /home/user/turantalim
source venv/bin/activate
pip install --upgrade django
pip freeze > requirements.txt
python manage.py migrate
sudo supervisorctl restart turantalim
```

### Update All Packages
```bash
cd /home/user/turantalim
source venv/bin/activate
pip list --outdated
pip install --upgrade -r requirements.txt
sudo supervisorctl restart turantalim
```

### Update System Packages
```bash
sudo apt update
sudo apt upgrade -y
sudo reboot  # If kernel updated
```

---

## 📝 Quick Tests

### Test API
```bash
# Health check
curl https://api.turantalim.uz/

# Login test
curl -X POST https://api.turantalim.uz/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+998901234567", "password": "testpass"}'

# Get test results (need token)
curl -X GET https://api.turantalim.uz/multilevel/test-results/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Admin Dashboard
```bash
# Check if accessible
curl -I https://api.turantalim.uz/admin-dashboard/

# Check static files
curl -I https://api.turantalim.uz/admin-dashboard/js/main.js
```

### Test Media Files
```bash
# Check media directory
ls -la /home/user/turantalim/media/

# Test access (if files exist)
curl -I https://api.turantalim.uz/media/writing/test.jpg
```

---

## 🎯 Production URLs

| Service | URL |
|---------|-----|
| API Base | https://api.turantalim.uz/ |
| Admin Dashboard | https://api.turantalim.uz/admin-dashboard/ |
| Django Admin | https://api.turantalim.uz/admin/ |
| API Docs | https://api.turantalim.uz/swagger/ |
| Media Files | https://api.turantalim.uz/media/ |

---

## 📞 Emergency Commands

### Stop Everything
```bash
sudo supervisorctl stop all
sudo systemctl stop nginx
```

### Start Everything
```bash
sudo systemctl start nginx
sudo supervisorctl start all
```

### Full Restart
```bash
sudo systemctl restart nginx
sudo supervisorctl restart all
sudo systemctl restart postgresql
sudo systemctl restart redis-server
```

---

**Keep this file handy for quick reference! 🚀**
