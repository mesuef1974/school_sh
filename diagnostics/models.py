
from django.db import models
from django.contrib.auth.models import Group

class AcademicYear(models.Model):
    name = models.CharField("السنة الدراسية", max_length=20, unique=True)
    start_date = models.DateField("تاريخ البدء", blank=True, null=True)
    end_date = models.DateField("تاريخ الانتهاء", blank=True, null=True)
    is_active = models.BooleanField("السنة النشطة", default=False)
    code = models.CharField("كود السنة", max_length=10, unique=True, editable=False)
    def __str__(self): return self.name
    class Meta:
        verbose_name = "سنة دراسية"
        verbose_name_plural = "السنوات الدراسية"
        ordering = ['-name']

class JobTitle(models.Model):
    title = models.CharField("المسمى الوظيفي", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود المسمى", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)
    groups = models.ManyToManyField(Group, blank=True, related_name="job_titles", verbose_name="مجموعات الصلاحيات")
    is_canonical = models.BooleanField("مسمى معتمد/رئيسي", default=False)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    def __str__(self): return self.title
    class Meta:
        verbose_name = "مسمى وظيفي"
        verbose_name_plural = "المسميات الوظيفية"