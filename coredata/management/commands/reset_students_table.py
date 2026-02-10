from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drops the students table and resets migration 0012 to allow a clean recreate.'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("Dropping old tables...")
            
            # 1. Drop the tables
            cursor.execute("DROP TABLE IF EXISTS students CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS coredata_historicalstudent CASCADE;")
            
            self.stdout.write(self.style.SUCCESS("Tables dropped."))

            # 2. Reset migration history for 0012
            self.stdout.write("Resetting migration history...")
            cursor.execute("DELETE FROM django_migrations WHERE app='coredata' AND name='0012_student_historicalstudent';")
            
            self.stdout.write(self.style.SUCCESS("Migration history cleaned."))
            
        self.stdout.write(self.style.SUCCESS("Done! Now run 'python manage.py migrate coredata'"))