
from .base import *
import os

DEBUG = False

# Allow all hosts for Vercel deployment
ALLOWED_HOSTS = ['*']

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# WhiteNoise configuration for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database configuration
# Note: SQLite on Vercel is ephemeral. For production, use PostgreSQL.
# If DATABASE_URL is set (e.g. from Vercel Postgres), use it.
import dj_database_url
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
        )
    }