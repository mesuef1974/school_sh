import os
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from coredata.models import Staff, JobTitle, FilePermission

class Command(BaseCommand):
    help = 'تطهير وتوحيد المسميات الوظيفية وربطها بنظام مجموعات Django (RBAC)'

    def handle(self, *args, **options):
        # 1. تعريف المسميات المعتمدة (Canonical) والمجموعات المرتبطة بها
        canonical_map = {
            "مدير المدرسة": {
                "keywords": ["مدير المدرسة", "مدير مدرسه"],
                "group": "الإدارة العليا",
            },
            "نائب المدير للشؤون الأكاديمية": {
                "keywords": ["النائب الاكاديمي", "نائب المدير للشؤون الاكاديمية", "نائب المدير للشؤون الأكاديمية", "النائب الأكاديمي"],
                "group": "الإدارة الوسطى",
            },
            "نائب المدير للشؤون الإدارية": {
                "keywords": ["النائب الاداري", "نائب المدير للشؤون الإدارية", "النائب الإداري"],
                "group": "الإدارة الوسطى",
            },
            "معلم": {
                "keywords": ["معلم", "مدرس", "معلمو", "مدرسو", "مدرسات", "محضر مختبر"],
                "group": "المعلمون",
            },
            "منسق مادة": {
                "keywords": ["منسق", "مسؤول مصادر", "مطور المنصة"],
                "group": "الإدارة الوسطى",
            },
            "أخصائي اجتماعي": {
                "keywords": ["أخصائي اجتماعي", "اخصائي اجتماعي", "الاخصائي الاجتماعي", "مرشد اكاديمي", "مرشد أكاديمي"],
                "group": "شؤون الطلاب",
            },
            "أخصائي نفسي": {
                "keywords": ["أخصائي نفسي", "اخصائي نفسي", "الاخصائي النفسي", "اخصائي تخاطب"],
                "group": "شؤون الطلاب",
            },
            "إداري": {
                "keywords": ["إداري", "اداري", "مشرف", "سكرتير", "موظف", "ملاحظ", "مرافق", "مندوب", "فني", "عامل", "محاسب", "امين مخزن", "أمين مخزن", "مخزن"],
                "group": "الموارد البشرية",
            },
            "ممرض": {
                "keywords": ["ممرض", "الممرض"],
                "group": "شؤون الطلاب",
            },
        }

        self.stdout.write(self.style.MIGRATE_HEADING("--- بدء عملية التطهير والتوحيد ---"))

        # 2. إنشاء المسميات المعتمدة وربطها بالمجموعات
        job_objects = {}
        for title, config in canonical_map.items():
            job, created = JobTitle.objects.get_or_create(title=title)
            job.is_canonical = True
            job.save()
            
            # ربط بمجموعة Django
            group_obj, g_created = Group.objects.get_or_create(name=config['group'])
            job.groups.add(group_obj)
            
            job_objects[title] = job
            self.stdout.write(f"المسمى المعتمد: {title} -> مجموعة: {config['group']}")

        # 3. إعادة توجيه الموظفين للمسميات المعتمدة
        all_staff = Staff.objects.all()
        for staff in all_staff:
            if not staff.job_title:
                continue
            
            old_title = staff.job_title.title
            new_job = None
            
            # البحث عن مطابقة في الكلمات المفتاحية
            for title, config in canonical_map.items():
                if any(kw in old_title for kw in config['keywords']):
                    new_job = job_objects[title]
                    break
            
            if new_job and staff.job_title != new_job:
                staff.job_title = new_job
                staff.save()
                
                # تحديث مستخدم Django وربطه بالمجموعة تلقائياً
                if staff.user:
                    for g in new_job.groups.all():
                        staff.user.groups.add(g)
                    staff.user.save()
                
                self.stdout.write(self.style.SUCCESS(f"تم تحديث: {staff.name} | من: {old_title} -> إلى: {new_job.title}"))

        # 4. تنظيف المسميات غير المعتمدة (التي لا يتبعها أي موظف الآن)
        non_canonical = JobTitle.objects.filter(is_canonical=False)
        for job in non_canonical:
            count = Staff.objects.filter(job_title=job).count()
            if count == 0:
                self.stdout.write(self.style.WARNING(f"حذف مسمى مكرر/غير مستخدم: {job.title}"))
                job.delete()
            else:
                self.stdout.write(self.style.NOTICE(f"مسمى يحتاج مراجعة (لا يزال مرتبطاً بـ {count} موظفين): {job.title}"))

        self.stdout.write(self.style.MIGRATE_LABEL("--- انتهت العملية بنجاح ---"))
