
from .base import *
import os
import dj_database_url

# --- DEBUGGING MODE: ON ---
# We force DEBUG=True to see the actual error on Vercel
DEBUG = True 

ALLOWED_HOSTS = ['*']

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False 

# WhiteNoise configuration
try:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
except ValueError:
    pass

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')

# Use simpler storage to avoid "Missing Manifest" errors
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files
MEDIA_ROOT = '/tmp/media'

# Database configuration
# Check if DATABASE_URL is set
if os.environ.get('DATABASE_URL'):
    try:
        db_config = dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
        DATABASES = {
            'default': db_config
        }
    except Exception as e:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': '/tmp/db.sqlite3',
            }
        }
else:
    # Fallback to SQLite in /tmp
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}