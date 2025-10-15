# 🚀 Turantalim - Deployment Documentation

---

## 📚 Documentation Index

Bu loyihaning to'liq deployment dokumentatsiyasi:

### 1️⃣ **Production Deployment Guide**
📄 [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- Full step-by-step production deployment
- Server setup
- SSL configuration
- Database setup
- Nginx & Gunicorn configuration

### 2️⃣ **Quick Setup Commands**
⚡ [QUICK_SETUP_COMMANDS.md](./QUICK_SETUP_COMMANDS.md)
- Copy-paste ready commands
- Monitoring commands
- Troubleshooting
- Maintenance tasks

### 3️⃣ **Frontend Integration**
🎯 [FRONTEND_INTEGRATION_README.md](./FRONTEND_INTEGRATION_README.md)
- Frontend (Nuxt3) integration guide
- Complete code examples
- Data structures
- Testing guide

### 4️⃣ **API Documentation**
📘 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Complete API reference
- Request/Response formats
- Authentication flow
- File upload guides

### 5️⃣ **API Quick Reference**
📝 [API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)
- Quick endpoint lookup
- Example requests
- Status codes
- Error handling

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TURANTALIM SYSTEM                            │
└─────────────────────────────────────────────────────────────────┘

                    Internet (HTTPS)
                          │
                          ↓
                 ┌────────────────┐
                 │   Nginx        │  Port 443 (SSL)
                 │   (Reverse     │  - Static files
                 │    Proxy)      │  - Media files
                 └────────────────┘  - Admin Dashboard
                          │
                          ↓
                 ┌────────────────┐
                 │   Gunicorn     │  Port 8000
                 │   (WSGI)       │  - Django app
                 └────────────────┘
                          │
                          ↓
        ┌─────────────────┴─────────────────┐
        │                                    │
        ↓                                    ↓
┌────────────────┐                  ┌────────────────┐
│  PostgreSQL    │                  │     Redis      │
│  (Database)    │                  │    (Cache)     │
└────────────────┘                  └────────────────┘
        │
        ↓
┌────────────────┐
│  Media Files   │
│  (User Uploads)│
└────────────────┘
```

---

## 🌐 Production URLs

| Service | URL | Description |
|---------|-----|-------------|
| **API Base** | `https://api.turantalim.uz/` | Main API endpoint |
| **Admin Dashboard** | `https://api.turantalim.uz/admin-dashboard/` | Review submissions |
| **Django Admin** | `https://api.turantalim.uz/admin/` | System administration |
| **API Docs** | `https://api.turantalim.uz/swagger/` | API documentation |
| **Media Files** | `https://api.turantalim.uz/media/` | User uploaded files |
| **Static Files** | `https://api.turantalim.uz/static/` | CSS, JS, images |

---

## 📁 Project Structure

```
turantalim/
├── admin_dashboard/          # Admin Dashboard (Static HTML/JS)
│   ├── index.html           # Submissions list
│   ├── submission.html      # Review page
│   ├── login.html
│   ├── js/
│   │   ├── main.js          # Main logic
│   │   └── api-client.js    # API calls
│   └── css/
│       └── styles.css
│
├── apps/                     # Django apps
│   ├── multilevel/          # Main exam app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── manual_review_views.py
│   │   ├── manual_review_serializers.py
│   │   └── urls.py
│   ├── users/
│   └── payment/
│
├── core/                     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── nginx/                    # Nginx configuration
│   └── turantalim.conf
│
├── supervisor/               # Supervisor configuration
│   └── turantalim.conf
│
├── logs/                     # Application logs
│   ├── gunicorn_access.log
│   ├── gunicorn_error.log
│   └── supervisor.log
│
├── media/                    # User uploaded files
│   ├── writing/
│   └── speaking/
│
├── static/                   # Collected static files
│
├── venv/                     # Python virtual environment
│
├── deploy.sh                 # Deployment script
├── gunicorn_config.py        # Gunicorn configuration
├── manage.py                 # Django management
├── requirements.txt          # Python dependencies
├── env.production.example    # Production environment variables
│
└── Documentation Files:
    ├── PRODUCTION_DEPLOYMENT.md
    ├── QUICK_SETUP_COMMANDS.md
    ├── FRONTEND_INTEGRATION_README.md
    ├── API_DOCUMENTATION.md
    ├── API_QUICK_REFERENCE.md
    ├── postman_collection.json
    ├── frontend.env.example
    └── nuxt.config.example.ts
```

---

## 🚀 Quick Start (Production)

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/your-repo/turantalim.git
cd turantalim

# 2. Follow detailed guide
cat PRODUCTION_DEPLOYMENT.md
```

### Regular Deployment

```bash
# Quick deploy with one command
./deploy.sh
```

---

## 🔑 Configuration Files

### Required Files in Production:

1. **`.env`** - Environment variables (copy from `env.production.example`)
2. **`gunicorn_config.py`** - Gunicorn configuration
3. **`/etc/nginx/sites-available/turantalim`** - Nginx configuration
4. **`/etc/supervisor/conf.d/turantalim.conf`** - Supervisor configuration

---

## 🔐 Security Checklist

Before going to production:

- [ ] Set `DEBUG=False` in `.env`
- [ ] Change `SECRET_KEY` to a random string
- [ ] Use strong database password
- [ ] Setup SSL certificate (Let's Encrypt)
- [ ] Configure firewall (UFW)
- [ ] Enable HTTPS redirect
- [ ] Set proper file permissions
- [ ] Configure CORS properly
- [ ] Setup regular backups
- [ ] Enable log rotation
- [ ] Setup monitoring alerts

---

## 📊 Scoring System

### Writing Section (75 points)
- **Task 1 (Letter):** 0-24.75 points (33%)
- **Task 2 (Essay):** 0-50.25 points (67%)
- **Total:** Sum of Task 1 + Task 2

### Speaking Section (75 points)
- **Combined score** for all 3 parts
- **Total:** 0-75 points

### Status Flow
```
pending → reviewing → checked
```

---

## 🛠️ Technology Stack

### Backend
- **Framework:** Django 4.2
- **API:** Django REST Framework
- **Database:** PostgreSQL
- **Cache:** Redis
- **WSGI Server:** Gunicorn
- **Web Server:** Nginx
- **Process Manager:** Supervisor
- **SSL:** Let's Encrypt (Certbot)

### Frontend (for integration)
- **Framework:** Nuxt 3
- **Language:** TypeScript
- **HTTP Client:** $fetch / axios

### Admin Dashboard
- **Type:** Static SPA
- **Language:** JavaScript (ES6+)
- **UI Framework:** Bootstrap 5
- **Icons:** Font Awesome
- **Image Viewer:** Lightbox2

---

## 📞 Support & Resources

### Documentation
- **Django:** https://docs.djangoproject.com/
- **DRF:** https://www.django-rest-framework.org/
- **Nginx:** https://nginx.org/en/docs/
- **Gunicorn:** https://docs.gunicorn.org/
- **Let's Encrypt:** https://letsencrypt.org/docs/

### Project Contacts
- **Backend Issues:** backend@turantalim.uz
- **Frontend Issues:** frontend@turantalim.uz
- **DevOps Issues:** devops@turantalim.uz

---

## 🔄 Deployment Workflow

### Development → Production

```bash
# 1. Develop locally
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "Add new feature"

# 2. Push to repository
git push origin feature/new-feature

# 3. Merge to main (after review)
git checkout main
git merge feature/new-feature
git push origin main

# 4. Deploy to production
ssh user@api.turantalim.uz
cd /home/user/turantalim
./deploy.sh
```

---

## 📈 Monitoring

### Health Checks

```bash
# Check all services
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status postgresql

# View logs
tail -f /home/user/turantalim/logs/gunicorn_error.log
```

### Metrics to Monitor

- CPU usage
- Memory usage
- Disk space
- Database connections
- Response times
- Error rates
- SSL certificate expiry

---

## 🐛 Common Issues

### 1. 502 Bad Gateway
**Cause:** Gunicorn not running  
**Fix:** `sudo supervisorctl restart turantalim`

### 2. Static files not loading
**Cause:** Not collected or wrong permissions  
**Fix:** Run `python manage.py collectstatic --noinput`

### 3. Database connection error
**Cause:** Wrong credentials or PostgreSQL not running  
**Fix:** Check `.env` file and PostgreSQL status

### 4. SSL certificate error
**Cause:** Certificate expired  
**Fix:** `sudo certbot renew --force-renewal`

See [QUICK_SETUP_COMMANDS.md](./QUICK_SETUP_COMMANDS.md) for detailed troubleshooting.

---

## 📝 Maintenance Tasks

### Daily
- Monitor logs for errors
- Check disk space
- Verify backups

### Weekly
- Review performance metrics
- Check for security updates
- Clean old log files

### Monthly
- Database optimization
- Update dependencies
- Security audit
- Test disaster recovery

---

## 🎯 Next Steps

1. **Read:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
2. **Setup:** Follow the step-by-step guide
3. **Deploy:** Use `deploy.sh` for updates
4. **Monitor:** Check logs regularly
5. **Maintain:** Follow maintenance schedule

---

## 📄 License & Credits

**Project:** Turantalim Exam System  
**Version:** 1.0.0  
**Last Updated:** October 8, 2025

---

**Good luck with your deployment! 🚀**
