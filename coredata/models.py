
from django.db import models
from django.conf import settings
from django.db.models import Max
from simple_history.models import HistoricalRecords
import datetime
import hashlib
import base64
import os
import uuid
import io
from PIL import Image
from django.core.files.base import ContentFile
from cryptography.fernet import Fernet
from django.contrib.auth.models import Group

# --- LAZY KEY LOADING ---
# This function will only be called when the Fernet key is needed,
# not when the models.py file is first loaded.
def get_fernet():
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

class EncryptedCharField(models.TextField):
    """
    An encrypted text field.
    The encryption key is derived from settings.SECRET_KEY and loaded lazily.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return get_fernet().decrypt(value.encode()).decode()
        except Exception:
            return value  # Fallback if not encrypted or key changed

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        return get_fernet().decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        return get_fernet().encrypt(str(value).encode()).decode()


# --- MODELS ---

class JobTitle(models.Model):
    title = models.CharField("المسمى الوظيفي", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود المسمى", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)
    groups = models.ManyToManyField(Group, blank=True, related_name="job_titles", verbose_name="مجموعات الصلاحيات")
    is_canonical = models.BooleanField("مسمى معتمد/رئيسي", default=False)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "مسمى وظيفي"
        verbose_name_plural = "المسميات الوظيفية"

class EvidenceFile(models.Model):
    name = models.CharField("اسم الملف", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود الملف", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("وصف الملف", blank=True, null=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "تصنيف دليل"
        verbose_name_plural = "تصنيفات الأدلة"

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
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"

class AcademicYear(models.Model):
    name = models.CharField("السنة الدراسية", max_length=20, unique=True)
    start_date = models.DateField("تاريخ البدء", blank=True, null=True)
    end_date = models.DateField("تاريخ الانتهاء", blank=True, null=True)
    is_active = models.BooleanField("السنة النشطة", default=False)
    code = models.CharField("كود السنة", max_length=10, unique=True, editable=False)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "سنة دراسية"
        verbose_name_plural = "السنوات الدراسية"
        ordering = ['-name']

class StrategicGoal(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="strategic_goals")
    title = models.TextField("الهدف الاستراتيجي")
    goal_no = models.CharField("رقم الهدف", max_length=50, blank=True, null=True)
    code = models.CharField("كود الهدف", max_length=50, unique=True, editable=False)

    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "هدف استراتيجي"
        verbose_name_plural = "الأهداف الاستراتيجية"

class OperationalGoal(models.Model):
    strategic_goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, related_name="operational_goals")
    title = models.TextField("مؤشر الأداء / الهدف التشغيلي")
    indicator_no = models.CharField("رقم المؤشر", max_length=50, blank=True, null=True)
    code = models.CharField("كود المؤشر", max_length=50, unique=True, editable=False)

    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "هدف تشغيلي / مؤشر"
        verbose_name_plural = "الأهداف التشغيلية / المؤشرات"

class Committee(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("اسم اللجنة", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود اللجنة", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="committees")
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "لجنة"
        verbose_name_plural = "اللجان"

def get_evidence_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    username = instance.user.username.replace(' ', '_')
    uuid_str = uuid.uuid4().hex[:8]
    year = datetime.date.today().year
    return f"evidence_vault/{year}/{username}/{uuid_str}.{ext}"

class EvidenceDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_evidence_files')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    evidence_type = models.ForeignKey(EvidenceFile, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    title = models.CharField("عنوان الملف", max_length=255)
    file = models.FileField("الملف", upload_to=get_evidence_upload_path)
    original_filename = models.CharField("اسم الملف الأصلي", max_length=255, blank=True, null=True, editable=False)
    file_size = models.PositiveIntegerField("حجم الملف (بايت)", blank=True, null=True, editable=False)
    file_hash = models.CharField("بصمة الملف (SHA-256)", max_length=64, blank=True, null=True, editable=False)
    tags = models.CharField("الوسوم (Tags)", max_length=255, blank=True, null=True)
    description = models.TextField("وصف الملف", blank=True, null=True)
    created_at = models.DateTimeField("تاريخ الرفع", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "وثيقة دليل"
        verbose_name_plural = "مستودع الأدلة"

class OperationalPlanItems(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="plan_items", null=True)
    strategic_goal_link = models.ForeignKey(StrategicGoal, on_delete=models.SET_NULL, null=True, blank=True)
    operational_goal_link = models.ForeignKey(OperationalGoal, on_delete=models.SET_NULL, null=True, blank=True)
    rank_name = models.CharField("المجال", max_length=255, blank=True, null=True, db_index=True)
    procedure = models.TextField("الإجراء التنفيذي", blank=True, null=True)
    code = models.CharField("كود الإجراء الذكي", max_length=50, unique=True, editable=False, null=True)
    executor = models.CharField("الجهة المنفذة (نصي)", max_length=255, blank=True, null=True)
    date_range = models.CharField("فترة التنفيذ", max_length=255, blank=True, null=True)
    follow_up = models.CharField("حالة المتابعة", max_length=255, blank=True, null=True)
    comments = models.TextField("الملاحظات والتحديات", blank=True, null=True)
    evidence_type = models.CharField("نوع الدليل", max_length=255, blank=True, null=True)
    evidence_source_employee = models.CharField("المقيّم", max_length=255, blank=True, null=True)
    evidence_source_file = models.CharField("موقع الدليل (نصي)", max_length=255, blank=True, null=True)
    evidence_document = models.ForeignKey(EvidenceDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name="linked_plan_items")
    evaluation = models.CharField("التقييم", max_length=255, blank=True, null=True)
    evaluation_notes = models.TextField("ملاحظات التقييم", blank=True, null=True)
    evidence_requested = models.BooleanField("طلب دليل؟", default=False)
    evidence_requested_at = models.DateTimeField("تاريخ طلب الدليل", blank=True, null=True)
    evidence_request_note = models.TextField("ملاحظة طلب الدليل", blank=True, null=True)
    last_review_date = models.DateTimeField("تاريخ آخر مراجعة", blank=True, null=True)
    digital_seal = models.CharField("بصمة النزاهة الرقمية", max_length=64, blank=True, null=True, editable=False)
    status = models.CharField("حالة البند", max_length=50, choices=[("Draft", "مسودة"), ("In Progress", "جاري التنفيذ"), ("Pending Review", "بانتظار المراجعة"), ("Completed", "مكتمل"), ("Returned", "مرفوض")], default="In Progress", blank=True, null=True, db_index=True)
    executor_committee = models.ForeignKey(Committee, on_delete=models.SET_NULL, verbose_name="اللجنة المنفذة", related_name="executed_plan_items", blank=True, null=True)
    evaluator_committee = models.ForeignKey(Committee, on_delete=models.SET_NULL, verbose_name="اللجنة المقيمة", related_name="evaluated_plan_items", blank=True, null=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.code or f"بند {self.id}"
    class Meta:
        verbose_name = "بند خطة تشغيلية"
        verbose_name_plural = "بنود الخطة التشغيلية"

class Student(models.Model):
    national_no = EncryptedCharField("الرقم الشخصي (QID)", unique=True)
    name_ar = models.CharField("اسم الطالب (عربي)", max_length=255)
    name_en = models.CharField("اسم الطالب (إنجليزي)", max_length=255, blank=True, null=True)
    date_of_birth = models.DateField("تاريخ الميلاد", blank=True, null=True)
    grade = models.CharField("الصف", max_length=10, db_index=True)
    section = models.CharField("الشعبة", max_length=10, db_index=True)
    needs = models.CharField("احتياجات خاصة", max_length=50, blank=True, null=True)
    parent_national_no = EncryptedCharField("رقم ولي الأمر الشخصي", blank=True, null=True)
    parent_name = models.CharField("اسم ولي الأمر", max_length=255, blank=True, null=True)
    parent_relation = models.CharField("صلة القرابة", max_length=50, blank=True, null=True)
    parent_phone = EncryptedCharField("رقم هاتف ولي الأمر", blank=True, null=True)
    parent_email = models.EmailField("بريد ولي الأمر", blank=True, null=True)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name_ar} ({self.grade}/{self.section})"
    class Meta:
        verbose_name = "طالب"
        verbose_name_plural = "الطلاب"
        ordering = ['grade', 'section', 'name_ar']

class GroupExtension(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='extension')
    axis1_name = models.CharField("اسم المحور 1", max_length=255, blank=True, default="المحور الأول")
    axis1_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis1_groups', verbose_name="مقيّمين محور 1", blank=True)
    axis2_name = models.CharField("اسم المحور 2", max_length=255, blank=True, default="المحور الثاني")
    axis2_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis2_groups', verbose_name="مقيّمين محور 2", blank=True)
    axis3_name = models.CharField("اسم المحور 3", max_length=255, blank=True, default="المحور الثالث")
    axis3_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis3_groups', verbose_name="مقيّمين محور 3", blank=True)
    axis4_name = models.CharField("اسم المحور 4", max_length=255, blank=True, default="المحور الرابع")
    axis4_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis4_groups', verbose_name="مقيّمين محور 4", blank=True)
    axis5_name = models.CharField("اسم المحور 5", max_length=255, blank=True, default="المحور الخامس")
    axis5_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis5_groups', verbose_name="مقيّمين محور 5", blank=True)
    axis6_name = models.CharField("اسم المحور 6", max_length=255, blank=True, default="المحور السادس")
    axis6_evaluators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='axis6_groups', verbose_name="مقيّمين محور 6", blank=True)

    def __str__(self):
        return f"Extension for {self.group.name}"