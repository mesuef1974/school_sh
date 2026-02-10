
#!/usr/bin/env python
import os
import sys

# --- Monkey Patch for Jazzmin + Django 5.x/6.x compatibility ---
# Fixes: TypeError: args or kwargs must be provided in format_html
import django.utils.html

original_format_html = django.utils.html.format_html

def patched_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return format_string
    return original_format_html(format_string, *args, **kwargs)

django.utils.html.format_html = patched_format_html
# ---------------------------------------------------------------

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()