import csv
import os
import re
from django.core.management.base import BaseCommand
from coredata.models import JobTitle, EvidenceFile, FilePermission, Staff

class Command(BaseCommand):
    help = 'Creates and links JobTitles, EvidenceFiles, and Permissions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n--- Step 1: Populating Files and Permissions from CSV ---"))
        self.populate_from_csv()

        self.stdout.write(self.style.SUCCESS("\n--- Data Population Complete! ---"))

    def populate_from_csv(self):
        """
        Reads the CSV to create EvidenceFiles and their permissions
        based on the JobTitles.
        """
        csv_path = r'/shaniya_django/الارشيف/Doc_School\ملفات المدرسة.csv'
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found at {csv_path}"))
            return

        # قاموس لتطبيع المسميات الوظيفية لتتطابق مع جدول الموظفين
        JOB_NORMALIZATION = {
            "الاخصائي الاجتماعي": "أخصائي اجتماعي",
            "اخصائي اجتماعي": "أخصائي اجتماعي",
            "الاخصائي النفسي": "اخصائي نفسي",
            "أمين المخزن": "امين مخزن",
            "المشرفون الاداريون": "مشرف إداري",
            "مدير المدرسة / النائب الاداري": "مدير مدرسة",
            "المرشد الاكاديمي": "مرشد أكاديمي",
            "السكرتير": "سكرتير مدرسة",
            "سكرتير": "سكرتير مدرسة",
            "النائب الاكاديمي": "نائب المدير للشؤون الأكاديمية",
            "ممرض المدرسة": "مرافق الدعم",
            "منسق الكيمياء": "منسق كيمياء",
            "منسق الفيزياء": "منسق فيزياء",
            "منسق الاحياء": "منسق احياء",
            "منسق العلوم": "منسق علوم",
            "منسق الرياضيات": "منسق رياضيات",
            "منسق الدراسات الاجتماعية": "منسق دراسات اجتماعية",
            "منسق التربية البدنية": "منسق تربية بدنية",
            "منسق اللغة الانجليزية": "منسق اللغة الإنجليزية",
            "منسق تكنولوجيا المعلومات": "منسق تكنولوجيا المعلومات",
            "منسق العلوم الشرعية": "منسق علوم شرعية",
            "منسق التربية الاسلامية": "منسق علوم شرعية",
        }

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            # Try semicolon first, then comma if it looks like comma
            content = f.read(1024)
            f.seek(0)
            dialect = ';' if ';' in content else ','
            reader = csv.DictReader(f, delimiter=dialect)
            
            for row in reader:
                raw_job = row.get('Pos')
                raw_file = row.get('Files')
                if not raw_job or not raw_file: continue

                job_title_text = raw_job.strip()
                file_name_text = raw_file.strip()

                # تطبيع المسمى الوظيفي
                normalized_job = JOB_NORMALIZATION.get(job_title_text, job_title_text).strip()

                # Get or create JobTitle
                job_title_obj, _ = JobTitle.objects.get_or_create(title=normalized_job)
                
                # Get or create EvidenceFile
                evidence_file_obj, _ = EvidenceFile.objects.get_or_create(name=file_name_text)
                
                # Create Permission
                # Important: Create direct permission first
                FilePermission.objects.update_or_create(
                    job_title=job_title_obj,
                    evidence_file=evidence_file_obj,
                    defaults={'can_view': True}
                )
                
                # Logic for Teachers: They should see files assigned to their coordinators
                if "منسق" in normalized_job:
                    # e.g. "منسق اللغة العربية" -> "معلم اللغة العربية"
                    teacher_title = normalized_job.replace("منسق", "معلم")
                    teacher_job_obj, _ = JobTitle.objects.get_or_create(title=teacher_title)
                    FilePermission.objects.update_or_create(
                        job_title=teacher_job_obj,
                        evidence_file=evidence_file_obj,
                        defaults={'can_view': True}
                    )
                    
                    # Also handle "مدرس" variant
                    mudaris_title = normalized_job.replace("منسق", "مدرس")
                    mudaris_job_obj, _ = JobTitle.objects.get_or_create(title=mudaris_title)
                    FilePermission.objects.update_or_create(
                        job_title=mudaris_job_obj,
                        evidence_file=evidence_file_obj,
                        defaults={'can_view': True}
                    )