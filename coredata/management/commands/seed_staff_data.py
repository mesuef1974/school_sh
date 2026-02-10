from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from coredata.models import Staff, JobTitle
import random

class Command(BaseCommand):
    help = 'Seeds initial test staff members linked to users.'

    def handle(self, *args, **options):
        # 1. Ensure we have Job Titles
        jobs = JobTitle.objects.all()
        if not jobs.exists():
            self.stdout.write(self.style.ERROR("No Job Titles found. Please run seed_hr_data first."))
            return

        # 2. Define Test Staff Data
        test_staff = [
            {"name": "سلطان الهاجري", "email": "sultan@test.com", "job": "مدير المدرسة", "username": "sultan_admin"},
            {"name": "أحمد محمد", "email": "ahmed@test.com", "job": "نائب المدير للشؤون الأكاديمية", "username": "ahmed_acad"},
            {"name": "خالد العلي", "email": "khaled@test.com", "job": "منسق مادة", "username": "khaled_coord"},
            {"name": "علي حسن", "email": "ali@test.com", "job": "معلم", "username": "ali_teacher"},
            {"name": "سارة جاسم", "email": "sara@test.com", "job": "معلم", "username": "sara_teacher"},
        ]

        for data in test_staff:
            # Create User
            user, u_created = User.objects.get_or_create(
                username=data['username'],
                email=data['email']
            )
            if u_created:
                user.set_password('pass1234')
                user.save()
                self.stdout.write(f"Created User: {user.username}")

            # Get Job object
            job_obj = JobTitle.objects.filter(title=data['job']).first()
            if not job_obj:
                job_obj = random.choice(jobs)

            # Create Staff Profile
            staff, s_created = Staff.objects.get_or_create(
                user=user,
                defaults={
                    'name': data['name'],
                    'job_title': job_obj,
                    'email': data['email'],
                    'nationality': 'QA' if 'سلطان' in data['name'] else 'EXP',
                    'national_no': f"290{data['username'][-4:] if len(data['username']) > 4 else '1234'}5678",
                }
            )
            
            if s_created:
                self.stdout.write(self.style.SUCCESS(f"Created Staff Profile: {staff.name} as {staff.job_title.title}"))

        self.stdout.write(self.style.SUCCESS("Staff Seeding Completed Successfully."))
