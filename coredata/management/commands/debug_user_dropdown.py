from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from coredata.models import Staff, JobTitle, EvidenceFile
from django.db.models import Q

class Command(BaseCommand):
    help = 'Debugs why the dropdown is empty for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('search_term', type=str, help='Name or username to search for')

    def handle(self, *args, **options):
        search_term = options['search_term']
        self.stdout.write(f"\n--- Checking for user/staff matching: '{search_term}' ---")
        
        # 1. Check Django User first (to see what we are dealing with)
        django_user = User.objects.filter(username__icontains=search_term).first()
        if django_user:
             self.stdout.write(f"✅ Found Django User: {django_user.username} (Email: {django_user.email})")
        else:
             self.stdout.write(f"⚠️ No Django User found matching '{search_term}' directly.")

        # 2. Check Staff Record
        staff = Staff.objects.filter(
            Q(name__icontains=search_term) | 
            Q(user_name__icontains=search_term) |
            Q(email__icontains=search_term)
        ).first()
        
        if not staff:
            self.stdout.write(self.style.ERROR(f"❌ No Staff record found matching '{search_term}'"))
            return

        self.stdout.write(f"✅ Found Staff: {staff.name} (ID: {staff.id})")
        self.stdout.write(f"   - User Name in Staff: {staff.user_name}")
        self.stdout.write(f"   - Email in Staff: {staff.email}")
        self.stdout.write(f"   - Job Number: {staff.job_number}")
        self.stdout.write(f"   - Job Title (Text): {staff.job_title}")
        
        # 3. Check Job Title Link
        if not staff.job_title_link:
            self.stdout.write(self.style.ERROR(f"❌ Job Title Link is NULL! This is the problem."))
            self.stdout.write(f"   The system doesn't know the ID of the job title for this user.")
            return
            
        self.stdout.write(f"✅ Job Title Link: {staff.job_title_link.title} (ID: {staff.job_title_link.id})")
        
        # 4. Check Permissions
        files_count = EvidenceFile.objects.filter(
            permitted_jobs__job_title=staff.job_title_link,
            permitted_jobs__can_view=True
        ).count()
        
        if files_count == 0:
            self.stdout.write(self.style.ERROR(f"❌ No files found for this job title! (Count: 0)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Found {files_count} allowed files for this job title."))
            # List first 5 files
            files = EvidenceFile.objects.filter(
                permitted_jobs__job_title=staff.job_title_link,
                permitted_jobs__can_view=True
            )[:5]
            for f in files:
                self.stdout.write(f"   - {f.name}")