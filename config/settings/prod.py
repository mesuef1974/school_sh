
from .base import *
import os

# FORCE DEBUG to be False in production, but allow override for troubleshooting
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Allow all hosts for Vercel deployment
ALLOWED_HOSTS = ['*']

# Security settings
# Vercel handles SSL termination, so we need to trust the headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Disable SSL Redirect to avoid infinite loops behind Vercel proxy
SECURE_SSL_REDIRECT = False 

# WhiteNoise configuration for static files
# Use a simpler storage backend to avoid "MissingFileError" during build
try:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
except ValueError:
    pass # Middleware might already be there

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Use simpler storage that doesn't require manifest generation (safer for Vercel)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Ensure static root exists
if not os.path.exists(STATIC_ROOT):
    os.makedirs(STATIC_ROOT)

# Database configuration
import dj_database_url

# Check if DATABASE_URL is set
if os.environ.get('DATABASE_URL'):
    try:
        DATABASES = {
            'default': dj_database_url.config(
                default=os.environ.get('DATABASE_URL'),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    except Exception as e:
        print(f"Error configuring database: {e}")
        # Fallback to SQLite if DB config fails (so the app at least starts)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
else:
    print("WARNING: DATABASE_URL not found, using SQLite")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Logging configuration to see errors in Vercel logs
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