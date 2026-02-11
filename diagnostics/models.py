
from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
import hashlib
import base64
from cryptography.fernet import Fernet

# --- LAZY KEY LOADING ---
def get_fernet():
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

class EncryptedCharField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None: return value
        try:
            return get_fernet().decrypt(value.encode()).decode()
        except Exception:
            return value

    def to_python(self, value):
        if value is None or isinstance(value, str): return value
        return get_fernet().decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None: return value
        return get_fernet().encrypt(str(value).encode()).decode()

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

class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff_profile")
    job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff_members")
    name = models.CharField("الاسم", max_length=255, db_index=True)
    code = models.CharField("كود الموظف الهيكلي", max_length=50, blank=True, null=True, unique=True, db_index=True)
    nationality = models.CharField("الجنسية", max_length=10, choices=[('QA', 'قطري'), ('EXP', 'مقيم')], default='EXP', db_index=True)
    job_number = models.CharField("الرقم الوظيفي", max_length=50, blank=True, null=True, unique=True, db_index=True)
    email = models.EmailField("البريد الإلكتروني", max_length=254, blank=True, null=True, unique=True, db_index=True)
    national_no = EncryptedCharField("الرقم الوطني", blank=True, null=True, unique=True)
    phone_no = EncryptedCharField("رقم الجوال", blank=True, null=True)
    account_no = EncryptedCharField("رقم الحساب", blank=True, null=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    def __str__(self): return self.name
    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"