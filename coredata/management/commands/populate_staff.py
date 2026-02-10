import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from coredata.models import Staff, JobTitle

class Command(BaseCommand):
    help = 'Populates Staff model and links them to Users based on CSV data.'

    def handle(self, *args, **options):
        csv_path = r'/shaniya_django/الارشيف/Doc_School\staff_data_from_db.csv'
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting staff population from {csv_path}..."))

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Print headers for debug
            headers = reader.fieldnames
            self.stdout.write(self.style.WARNING(f"Headers found: {headers}"))
            count = 0
            linked = 0
            
            for row in reader:
                name = row['name'].strip()
                job_title_name = row['job_title'].strip()

                # Get or create JobTitle
                job_title_obj, _ = JobTitle.objects.get_or_create(title=job_title_name)

                # Create or update Staff
                staff, created = Staff.objects.update_or_create(
                    name=name,
                    defaults={'job_title': job_title_obj}
                )
                
                # Try to link to a User
                # Strategy 1: Match first name or full name in User's first_name/last_name
                user = User.objects.filter(first_name__icontains=name).first()
                if not user:
                     # Strategy 2: If name is short (like 'Nurse'), try exact username
                     user = User.objects.filter(username__iexact=name).first()
                
                if user:
                    staff.user = user
                    staff.save()
                    linked += 1
                
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished. Total Staff: {count}, Linked to Users: {linked}"))