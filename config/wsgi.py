
import os
import sys
from django.core.wsgi import get_wsgi_application
import django.utils.html

# --- Monkey Patch for Jazzmin + Django 5.x/6.x compatibility ---
original_format_html = django.utils.html.format_html

def patched_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return format_string
    return original_format_html(format_string, *args, **kwargs)

django.utils.html.format_html = patched_format_html
# ---------------------------------------------------------------

# Use 'config.settings.prod' in production
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
app = application

# --- Vercel SQLite Fix: Auto-migrate on startup if DB is missing ---
# This is only for demo purposes on Vercel without a real DB.
try:
    from django.conf import settings
    import glob
    
    # Check if we are using SQLite and running on Vercel (Lambda)
    is_sqlite = settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
    
    if is_sqlite:
        db_path = settings.DATABASES['default']['NAME']
        # If DB file doesn't exist or is empty (0 bytes), run migrate
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            print("SQLite DB missing or empty. Running migrations...")
            from django.core.management import call_command
            call_command('migrate')
            print("Migrations completed.")
            
            # Optional: Create a superuser for access if needed
            # from django.contrib.auth import get_user_model
            # User = get_user_model()
            # if not User.objects.filter(username='admin').exists():
            #     User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            
except Exception as e:
    print(f"Auto-migration failed: {e}")
# -------------------------------------------------------------------