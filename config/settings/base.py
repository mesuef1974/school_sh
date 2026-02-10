
from pathlib import Path
import environ
import os
from django.utils.translation import gettext_lazy as _

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-secret-key-change-me')
DEBUG = env('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework', # Added Django REST Framework
    'django_htmx',
    'tailwind',
    'theme',
    'rangefilter',
    'import_export',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',

    'simple_history', # Full Audit Logging

    # Local apps
    'coredata',
    'project_memory',
]


TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # Keep it here
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware', # Tracking Who made the change
    'django_htmx.middleware.HtmxMiddleware',
]


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'coredata' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'school_test',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5434',
        'OPTIONS': {
            'sslmode': 'prefer',
        }
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
TIME_ZONE = env('TZ', default='Asia/Qatar')
USE_I18N = True
USE_TZ = True

# --- Static files (CSS, JavaScript, Images) ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    # Explicitly add the theme's static directory
    BASE_DIR / "theme" / "static",
    # Add the general static directory for brand assets etc.
    BASE_DIR / "coredata" / "static",
]
# --- END Static files ---

# --- Media Files (User Uploads) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# --- END Media Files ---

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'plan_list'
LOGOUT_REDIRECT_URL = 'login'

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

JAZZMIN_SETTINGS = {
    "site_title": "إدارة منصة الشحانية",
    "site_header": "منصة الشحانية",
    "site_brand": "الشحانية الذكية",
    "site_logo": "brand/logo.png",
    "login_logo": "brand/logo.png",
    "login_logo_dark": "brand/logo.png",
    "site_logo_classes": "img-circle",
    "topmenu_links": [
        {"name": "الرئيسية",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "صحة المنصة", "url": "/health/", "new_window": True, "permissions": ["auth.view_user"]},
        {"name": "عرض الموقع", "url": "/", "new_window": True},
        {"model": "auth.user"},
    ],
    "usermenu_links": [
        {"name": "عرض الموقع", "url": "/", "new_window": True},
        {"model": "auth.user"}
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "language_chooser": True,
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-white",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}