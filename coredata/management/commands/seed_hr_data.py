from django.core.management.base import BaseCommand
from coredata.models import JobTitle, EvidenceFile, FilePermission

class Command(BaseCommand):
    help = 'Seeds initial HR data (Job Titles, Evidence Files, and Permissions)'

    def handle(self, *args, **options):
        # 1. Seed Job Titles
        job_titles = [
            {"title": "مدير النظام", "description": "مسؤول تقني عن المنصة"},
            {"title": "مدير المدرسة", "description": "المسؤول الأول عن الإدارة المدرسية"},
            {"title": "نائب المدير للشؤون الأكاديمية", "description": "الإشراف على العملية التعليمية"},
            {"title": "نائب المدير للشؤون الإدارية", "description": "الإشراف على الجوانب الإدارية والمالية"},
            {"title": "منسق مادة", "description": "الإشراف على قسم تخصصي"},
            {"title": "معلم", "description": "كادر تعليمي"},
            {"title": "أخصائي اجتماعي", "description": "متابعة الحالات الطلابية"},
            {"title": "أخصائي نفسي", "description": "الدعم النفسي والتربوي"},
            {"title": "إداري", "description": "موظف إداري"},
        ]

        created_jobs = {}
        for job_data in job_titles:
            job, created = JobTitle.objects.get_or_create(
                title=job_data['title'],
                defaults={'description': job_data['description']}
            )
            created_jobs[job.title] = job
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Job Title: {job.title}"))

        # 2. Seed Evidence File Categories
        evidence_categories = [
            {"name": "سجل الحضور والغياب"},
            {"name": "الخطة الأسبوعية"},
            {"name": "تحضير الدروس"},
            {"name": "تقرير الأداء الوظيفي"},
            {"name": "ملف الأدلة السنوي"},
            {"name": "كشف درجات الطلاب"},
            {"name": "سجل الاجتماعات"},
        ]

        created_files = {}
        for file_data in evidence_categories:
            ef, created = EvidenceFile.objects.get_or_create(
                name=file_data['name']
            )
            created_files[ef.name] = ef
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Evidence Category: {ef.name}"))

        # 3. Map Default Permissions
        # (JobTitle Title -> List of Evidence File Names)
        permissions_map = {
            "مدير المدرسة": list(created_files.keys()), # Everything
            "نائب المدير للشؤون الأكاديمية": ["الخطة الأسبوعية", "تحضير الدروس", "كشف درجات الطلاب", "سجل الاجتماعات"],
            "منسق مادة": ["الخطة الأسبوعية", "تحضير الدروس", "كشف درجات الطلاب"],
            "معلم": ["الخطة الأسبوعية", "تحضير الدروس"],
        }

        for job_title, allowed_files in permissions_map.items():
            job_obj = created_jobs.get(job_title)
            if not job_obj: continue

            for file_name in allowed_files:
                ef_obj = created_files.get(file_name)
                if not ef_obj: continue

                perm, created = FilePermission.objects.get_or_create(
                    job_title=job_obj,
                    evidence_file=ef_obj,
                    defaults={'can_view': True}
                )
                if created:
                    self.stdout.write(f"Permission Mapped: {job_title} -> {file_name}")

        self.stdout.write(self.style.SUCCESS("HR Seeding Completed Successfully."))
