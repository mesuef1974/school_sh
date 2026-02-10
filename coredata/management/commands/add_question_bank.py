from django.core.management.base import BaseCommand
from coredata.models import JobTitle, EvidenceFile, FilePermission

class Command(BaseCommand):
    help = 'Adds "Question Bank" file and assigns it to specific coordinators'

    def handle(self, *args, **options):
        file_name = "بنك الأسئلة"
        
        # 1. Create or Get the File
        evidence_file, created = EvidenceFile.objects.get_or_create(name=file_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new file: '{file_name}'"))
        else:
            self.stdout.write(f"File '{file_name}' already exists.")

        # 2. List of Job Titles to assign
        target_titles = [
            "منسق تكنولوجيا المعلومات",
            "منسق اللغة العربية",
            "منسق اللغة الإنجليزية",
            "منسق الكيمياء",
            "منسق الفيزياء",
            "منسق الفنون البصرية",
            "منسق العلوم",
            "منسق الرياضيات",
            "منسق الدراسات الاجتماعية",
            "منسق التربية الخاصة",
            "منسق التربية البدنية",
            "منسق التربية الاسلامية",
            "منسق الاحياء"
        ]

        self.stdout.write("\nAssigning permissions...")
        
        assigned_count = 0
        not_found_count = 0

        for title in target_titles:
            # Try to find the job title (exact match first)
            try:
                job_title = JobTitle.objects.get(title=title)
                
                # Create Permission
                perm, perm_created = FilePermission.objects.get_or_create(
                    job_title=job_title,
                    evidence_file=evidence_file,
                    defaults={'can_view': True}
                )
                
                if perm_created:
                    self.stdout.write(self.style.SUCCESS(f"✅ Assigned to: {title}"))
                else:
                    self.stdout.write(f"ℹ️ Already assigned to: {title}")
                
                assigned_count += 1

            except JobTitle.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Job Title not found: {title}"))
                not_found_count += 1

        self.stdout.write("\n-----------------------------------")
        self.stdout.write(f"Total Assigned: {assigned_count}")
        if not_found_count > 0:
            self.stdout.write(self.style.WARNING(f"Total Not Found: {not_found_count}"))
        else:
            self.stdout.write(self.style.SUCCESS("All assignments completed successfully."))