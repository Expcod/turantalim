from .base import *  # noqa


DEBUG = True

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'turantalim_db',
        'USER': 'turan_user',
        'PASSWORD': 'cwhnsis98',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
# CORS

# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_HEADERS = ["*"]
