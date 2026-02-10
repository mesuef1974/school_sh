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
import img2pdf
from django.core.files.base import ContentFile
from cryptography.fernet import Fernet
import sys
from django.contrib.auth.models import Group

# Try to import pypdf for PDF compression (Optional)
try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import PdfReadError
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from PyPDF2.errors import PdfReadError
    except ImportError:
        PdfReader = None

# -----------------------------------------------------------------------------
# The new, clean, and canonical data model for the Shaniya Platform.
# All other models have been removed.
# All models here are managed by Django (managed = True).
# -----------------------------------------------------------------------------


class JobTitle(models.Model):
    """
    جدول المسميات الوظيفية الموحد.
    يمثل كل مسمى وظيفي محتمل في المدرسة.
    """
    title = models.CharField("المسمى الوظيفي", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود المسمى", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            # Smart Latin Code Generation
            term_map = {
                "معلم": "TCH", "منسق": "COORD", "مدرس": "TCH", "مدير": "DIR", "وكيل": "VP",
                "رياضيات": "MATH", "علوم": "SCI", "عربي": "ARAB", "انجليزي": "ENG",
                "اسلامية": "ISL", "بدنية": "PE", "فنية": "ART", "حاسوب": "IT",
                "اجتماعيات": "SOC", "نفسي": "PSY", "اجتماعي": "SW", "إداري": "ADM"
            }
            
            # Try to match keywords in the title
            code_parts = []
            for ar_term, en_code in term_map.items():
                if ar_term in self.title:
                    code_parts.append(en_code)
            
            prefix = "-".join(code_parts) if code_parts else "JOB"
            timestamp = int(datetime.datetime.now().timestamp()) % 1000
            self.code = f"{prefix}-{self.id if self.id else JobTitle.objects.count() + 1}-{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})" if self.code else self.title

    class Meta:
        managed = True
        db_table = 'job_titles'
        verbose_name = "مسمى وظيفي"
        verbose_name_plural = "المسميات الوظيفية"

    history = HistoricalRecords()


class EvidenceFile(models.Model):
    """
    جدول ملفات الأدلة (التصنيف).
    يحتوي على قائمة بجميع أنواع الملفات المعتمدة (مثل: سجل الحضور، الخطة الأسبوعية).
    """
    name = models.CharField("اسم الملف", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود الملف", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("وصف الملف", blank=True, null=True)

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            # Latin Code Generation for Evidence Files
            term_map = {
                "سجل": "REG", "ملف": "FILE", "خطة": "PLAN", "تقرير": "REP", "كشف": "LIST",
                "طلاب": "STU", "معلمين": "TCH", "منسق": "COORD", "نشاط": "ACT",
                "تحضير": "PREP", "أدلة": "EVID", "محور": "AXIS", "مجال": "AREA"
            }
            
            code_parts = []
            for ar_term, en_code in term_map.items():
                if ar_term in self.name:
                    code_parts.append(en_code)
            
            prefix = "-".join(code_parts) if code_parts else "FILE"
            timestamp = int(datetime.datetime.now().timestamp()) % 1000
            self.code = f"{prefix}-{self.id if self.id else EvidenceFile.objects.count() + 1}-{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

    class Meta:
        managed = True
        db_table = 'evidence_files'
        verbose_name = "تصنيف دليل"
        verbose_name_plural = "تصنيفات الأدلة"

    history = HistoricalRecords()


class FilePermission(models.Model):
    """
    جدول صلاحيات الملفات.
    يربط بين المسمى الوظيفي والملفات التي يحق له التعامل معها.
    """
    job_title = models.ForeignKey(JobTitle, on_delete=models.CASCADE, related_name='file_permissions', verbose_name="المسمى الوظيفي")
    evidence_file = models.ForeignKey(EvidenceFile, on_delete=models.CASCADE, related_name='permitted_jobs', verbose_name="الملف")
    can_view = models.BooleanField("صلاحية العرض", default=True)

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def __str__(self):
        return f"{self.job_title} -> {self.evidence_file}"

    class Meta:
        managed = True
        db_table = 'file_permissions'
        verbose_name = "صلاحية ملف"
        verbose_name_plural = "صلاحيات الملفات"
        unique_together = ('job_title', 'evidence_file')


# --- Custom Encrypted Field ---
class EncryptedCharField(models.TextField):
    """
    حقل نصي يقوم بتشفير البيانات آلياً قبل حفظها في قاعدة البيانات.
    """
    def __init__(self, *args, **kwargs):
        # We generate a key based on settings.SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key))
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None: return value
        try:
            return self.fernet.decrypt(value.encode()).decode()
        except Exception:
            return value # Fallback if not encrypted

    def to_python(self, value):
        if value is None or isinstance(value, str): return value
        return self.fernet.decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None: return value
        return self.fernet.encrypt(str(value).encode()).decode()

class Staff(models.Model):
    """
    جدول الموظفين.
    يحتوي على معلومات الموظف ويربطه بنظام المستخدمين والمسمى الوظيفي.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="حساب المستخدم",
        related_name="staff_profile"
    )
    job_title = models.ForeignKey(
        JobTitle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="المسمى الوظيفي",
        related_name="staff_members"
    )
    name = models.CharField("الاسم", max_length=255, db_index=True)
    code = models.CharField("كود الموظف الهيكلي", max_length=50, blank=True, null=True, unique=True, db_index=True)
    nationality = models.CharField(
        "الجنسية", 
        max_length=10, 
        choices=[('QA', 'قطري'), ('EXP', 'مقيم')], 
        default='EXP',
        db_index=True
    )
    job_number = models.CharField("الرقم الوظيفي", max_length=50, blank=True, null=True, unique=True, db_index=True)
    email = models.EmailField("البريد الإلكتروني", max_length=254, blank=True, null=True, unique=True, db_index=True)
    national_no = EncryptedCharField("الرقم الوطني", blank=True, null=True, unique=True)
    phone_no = EncryptedCharField("رقم الجوال", blank=True, null=True)
    account_no = EncryptedCharField("رقم الحساب", blank=True, null=True)
    
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            # Generate code: STF-{Year}-{NAT}-{JobCode}-{Seq}
            year_part = self.created_at.strftime('%y') if self.created_at else datetime.date.today().strftime('%y')
            nat_part = self.nationality
            job_part = self.job_title.code if self.job_title and self.job_title.code else "GEN"
            
            # Using timestamp + ID to ensure absolute uniqueness during migration
            timestamp = int(datetime.datetime.now().timestamp()) % 10000
            temp_id = self.id if self.id else Staff.objects.count() + 1
            self.code = f"STF-{year_part}-{nat_part}-{job_part}-{temp_id:03d}-{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

    class Meta:
        managed = True
        db_table = 'staff'
        verbose_name = "موظف"
        verbose_name_plural = "الموظفون"

    history = HistoricalRecords()


class AcademicYear(models.Model):
    """
    جدول السنوات الدراسية (مثل 2025-2026).
    """
    name = models.CharField("السنة الدراسية", max_length=20, unique=True, help_text="مثال: 2025-2026")
    start_date = models.DateField("تاريخ البدء", blank=True, null=True)
    end_date = models.DateField("تاريخ الانتهاء", blank=True, null=True)
    is_active = models.BooleanField("السنة النشطة", default=False)
    code = models.CharField("كود السنة", max_length=10, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            # Generate code like 2526 from 2025-2026
            parts = self.name.split('-')
            if len(parts) == 2:
                self.code = parts[0][-2:] + parts[1][-2:]
            else:
                self.code = self.name[:4]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "سنة دراسية"
        verbose_name_plural = "السنوات الدراسية"
        ordering = ['-name']


class StrategicGoal(models.Model):
    """
    الأهداف الاستراتيجية الكبرى.
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, verbose_name="السنة الدراسية", related_name="strategic_goals")
    title = models.TextField("الهدف الاستراتيجي")
    goal_no = models.CharField("رقم الهدف", max_length=50, blank=True, null=True)
    code = models.CharField("كود الهدف", max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = f"STRAT-{self.academic_year.code}"
            max_id = StrategicGoal.objects.filter(academic_year=self.academic_year).aggregate(max_id=Max('id'))['max_id'] or 0
            self.code = f"{prefix}-{(max_id + 1):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.title[:50]}..."

    class Meta:
        verbose_name = "هدف استراتيجي"
        verbose_name_plural = "الأهداف الاستراتيجية"


class OperationalGoal(models.Model):
    """
    الأهداف التشغيلية (المؤشرات).
    """
    strategic_goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, verbose_name="الهدف الاستراتيجي", related_name="operational_goals")
    title = models.TextField("مؤشر الأداء / الهدف التشغيلي")
    indicator_no = models.CharField("رقم المؤشر", max_length=50, blank=True, null=True)
    code = models.CharField("كود المؤشر", max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = f"OPER-{self.strategic_goal.code.split('-', 1)[1]}"
            max_id = OperationalGoal.objects.filter(strategic_goal=self.strategic_goal).aggregate(max_id=Max('id'))['max_id'] or 0
            self.code = f"{prefix}-{(max_id + 1):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.title[:50]}..."

    class Meta:
        verbose_name = "هدف تشغيلي / مؤشر"
        verbose_name_plural = "الأهداف التشغيلية / المؤشرات"


class Committee(models.Model):
    """
    يمثل لجنة أو فريق عمل أو قسم في المدرسة.
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="السنة الدراسية")
    name = models.CharField("اسم اللجنة", max_length=255, unique=True, db_index=True)
    code = models.CharField("كود اللجنة", max_length=50, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="الأعضاء",
        blank=True,
        related_name="committees"
    )
    strategic_goals_link = models.ManyToManyField(
        'project_memory.ProjectGoal',
        verbose_name="الأهداف الاستراتيجية المرتبطة",
        blank=True,
        related_name="responsible_committees"
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            year_part = self.academic_year.code if self.academic_year else "XXXX"
            temp_id = self.id if self.id else Committee.objects.count() + 1
            self.code = f"COM-{year_part}-{temp_id:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

    class Meta:
        managed = True
        db_table = 'committees'
        verbose_name = "لجنة"
        verbose_name_plural = "اللجان"

    history = HistoricalRecords()


def get_evidence_upload_path(instance, filename):
    """
    Generates a secure and organized path for uploaded evidence files.
    Format: evidence_vault/{year}/{username}/{uuid}_{slug}.ext
    """
    ext = filename.split('.')[-1]
    # Clean username to be filesystem safe
    username = instance.user.username.replace(' ', '_')
    # Generate a short UUID
    uuid_str = uuid.uuid4().hex[:8]
    # Get current year
    year = datetime.date.today().year
    
    return f"evidence_vault/{year}/{username}/{uuid_str}.{ext}"

class EvidenceDocument(models.Model):
    """
    مستودع ملفات الأدلة (خزنة ملفاتي).
    يربط الملفات بالمستخدم والسنة الدراسية مع معايير أرشفة عالية.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_evidence_files', verbose_name="المستخدم")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="السنة الدراسية")
    
    # Link to the EvidenceFile catalog
    evidence_type = models.ForeignKey(
        EvidenceFile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="تصنيف الدليل",
        related_name="documents",
        help_text="اختر نوع الملف (مثلاً: سجل حضور، خطة أسبوعية...)"
    )

    title = models.CharField("عنوان الملف", max_length=255)
    file = models.FileField("الملف", upload_to=get_evidence_upload_path)
    
    # Metadata for Professional Archiving
    original_filename = models.CharField("اسم الملف الأصلي", max_length=255, blank=True, null=True, editable=False)
    file_size = models.PositiveIntegerField("حجم الملف (بايت)", blank=True, null=True, editable=False)
    file_hash = models.CharField("بصمة الملف (SHA-256)", max_length=64, blank=True, null=True, editable=False)
    tags = models.CharField("الوسوم (Tags)", max_length=255, blank=True, null=True, help_text="كلمات مفتاحية مفصولة بفاصلة لسهولة البحث")
    
    description = models.TextField("وصف الملف", blank=True, null=True)
    
    created_at = models.DateTimeField("تاريخ الرفع", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-extract metadata on save
        if self.file:
            if not self.original_filename:
                self.original_filename = self.file.name
            
            ext = os.path.splitext(self.file.name)[1].lower()
            
            # --- 1. Smart Image Converter (Image -> PDF) ---
            try:
                if ext in ['.jpg', '.jpeg', '.png']:
                    # Open image
                    image = Image.open(self.file)
                    
                    # Convert to RGB (Keep Colors)
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    
                    # --- Golden Zone Optimization ---
                    # 1. Resize to max 1240px (A4 width @ ~100 DPI)
                    max_size = (1240, 1240)
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save to bytes buffer as PDF
                    pdf_bytes = io.BytesIO()
                    
                    # 2. Quality 40 (Good balance)
                    image.save(pdf_bytes, format='PDF', resolution=96.0, quality=40, optimize=True)
                    
                    # Create new ContentFile
                    new_filename = os.path.splitext(self.file.name)[0] + ".pdf"
                    self.file.save(new_filename, ContentFile(pdf_bytes.getvalue()), save=False)
                    
                    # Update metadata
                    self.original_filename = self.original_filename # Keep original name for reference
                    self.description = (self.description or "") + f" [Converted to Compressed PDF]"
                    
                    # Update extension for next steps
                    ext = '.pdf'
            except Exception as e:
                print(f"Image conversion failed: {e}")
                pass

            # --- 2. PDF Optimizer (Native PDF -> Compressed PDF) ---
            # Only if pypdf is installed
            if ext == '.pdf' and PdfReader:
                try:
                    # Read PDF
                    if self.file.closed:
                        self.file.open()
                    self.file.seek(0)
                    
                    reader = PdfReader(self.file)
                    writer = PdfWriter()
                    
                    # Add all pages to writer
                    for page in reader.pages:
                        writer.add_page(page)
                    
                    # Compress content streams (lossless)
                    for page in writer.pages:
                        page.compress_content_streams()
                    
                    # Save compressed PDF
                    pdf_bytes = io.BytesIO()
                    writer.write(pdf_bytes)
                    
                    # Replace file if smaller
                    if pdf_bytes.getbuffer().nbytes < self.file.size:
                        self.file.save(self.file.name, ContentFile(pdf_bytes.getvalue()), save=False)
                        self.description = (self.description or "") + f" [Optimized PDF]"
                except Exception as e:
                    print(f"PDF optimization failed: {e}")
                    pass

            try:
                self.file_size = self.file.size
            except:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        managed = True
        db_table = 'evidence_documents'
        verbose_name = "وثيقة دليل"
        verbose_name_plural = "مستودع الأدلة"


class OperationalPlanItems(models.Model):
    """
    النموذج المركزي لبنود الخطة التشغيلية.
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, verbose_name="السنة الدراسية", related_name="plan_items", null=True)
    strategic_goal_link = models.ForeignKey(StrategicGoal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الهدف الاستراتيجي المرتبط")
    operational_goal_link = models.ForeignKey(OperationalGoal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الهدف التشغيلي / المؤشر")
    
    rank_name = models.CharField("المجال", max_length=255, blank=True, null=True, db_index=True)
    
    # Keeping old fields for legacy/import data, but linking to new models
    year = models.IntegerField("السنة (قديم)", blank=True, null=True, db_index=True)
    target_no = models.CharField("رقم الهدف", max_length=50, blank=True, null=True, db_index=True)
    target = models.TextField("الهدف الاستراتيجي", blank=True, null=True)
    indicator_no = models.CharField("رقم المؤشر", max_length=50, blank=True, null=True, db_index=True)
    indicator = models.TextField("مؤشر الأداء", blank=True, null=True)
    
    procedure_no = models.CharField("رقم الإجراء", max_length=50, blank=True, null=True, db_index=True)
    procedure = models.TextField("الإجراء التنفيذي", blank=True, null=True)
    code = models.CharField("كود الإجراء الذكي", max_length=50, unique=True, editable=False, null=True)
    
    executor = models.CharField("الجهة المنفذة (نصي)", max_length=255, blank=True, null=True, db_index=True)
    date_range = models.CharField("فترة التنفيذ", max_length=255, blank=True, null=True)
    follow_up = models.CharField("حالة المتابعة", max_length=255, blank=True, null=True, db_index=True)
    comments = models.TextField("الملاحظات والتحديات", blank=True, null=True)
    evidence_type = models.CharField("نوع الدليل", max_length=255, blank=True, null=True)
    evidence_source_employee = models.CharField("المقيّم", max_length=255, blank=True, null=True)
    
    # Legacy field for manual path
    evidence_source_file = models.CharField("موقع الدليل (نصي)", max_length=255, blank=True, null=True)
    
    # New linked field for Evidence Document
    evidence_document = models.ForeignKey(
        EvidenceDocument,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="ملف الدليل المرفق",
        related_name="linked_plan_items",
        help_text="اختر ملفاً من مستودع ملفاتك"
    )

    evaluation = models.CharField("التقييم", max_length=255, blank=True, null=True, db_index=True)
    evaluation_notes = models.TextField("ملاحظات التقييم", blank=True, null=True)
    
    # --- New Fields for Review Workflow ---
    evidence_requested = models.BooleanField("طلب دليل؟", default=False)
    evidence_requested_at = models.DateTimeField("تاريخ طلب الدليل", blank=True, null=True)
    evidence_request_note = models.TextField("ملاحظة طلب الدليل", blank=True, null=True)
    
    last_review_date = models.DateTimeField("تاريخ آخر مراجعة", blank=True, null=True)
    digital_seal = models.CharField("بصمة النزاهة الرقمية", max_length=64, blank=True, null=True, editable=False)
    status = models.CharField(
        "حالة البند",
        max_length=50,
        choices=[
            ("Draft", "مسودة"),
            ("In Progress", "جاري التنفيذ"),
            ("Pending Review", "بانتظار المراجعة"),
            ("Completed", "مكتمل"),
            ("Returned", "مرفوض"),
        ],
        default="In Progress",
        blank=True, null=True,
        db_index=True
    )
    executor_committee = models.ForeignKey(
        'Committee',
        on_delete=models.SET_NULL,
        verbose_name="اللجنة المنفذة",
        related_name="executed_plan_items",
        blank=True, null=True
    )
    evaluator_committee = models.ForeignKey(
        'Committee',
        on_delete=models.SET_NULL,
        verbose_name="اللجنة المقيمة",
        related_name="evaluated_plan_items",
        blank=True, null=True
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True, null=True)

    def generate_seal(self):
        """
        Generates a SHA-256 hash of the item's key evidence data.
        """
        # Include the linked document in the seal if present
        doc_part = str(self.evidence_document.id) if self.evidence_document else self.evidence_source_file
        content = f"{self.code}{self.procedure}{self.follow_up}{doc_part}{self.evaluation}"
        return hashlib.sha256(content.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = "PROC"
            year_part = self.academic_year.code if self.academic_year else "XXXX"
            temp_id = self.id if self.id else OperationalPlanItems.objects.count() + 1
            self.code = f"{prefix}-{year_part}-{temp_id:04d}"
        
        # Evidence Hashing logic
        if self.status == 'Completed' and not self.digital_seal:
            self.digital_seal = self.generate_seal()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.procedure[:50]}..." if self.code else f"بند {self.id}"

    class Meta:
        managed = True
        db_table = 'operational_plan_items'
        verbose_name = "بند خطة تشغيلية"
        verbose_name_plural = "بنود الخطة التشغيلية"

    history = HistoricalRecords()


class Student(models.Model):
    """
    جدول الطلاب.
    يحتوي على البيانات الأساسية والأكاديمية وبيانات ولي الأمر.
    """
    # البيانات الأساسية
    national_no = EncryptedCharField("الرقم الشخصي (QID)", unique=True)
    name_ar = models.CharField("اسم الطالب (عربي)", max_length=255)
    name_en = models.CharField("اسم الطالب (إنجليزي)", max_length=255, blank=True, null=True)
    date_of_birth = models.DateField("تاريخ الميلاد", blank=True, null=True)
    
    # البيانات الأكاديمية
    grade = models.CharField("الصف", max_length=10, db_index=True) # 7, 8, 9...
    section = models.CharField("الشعبة", max_length=10, db_index=True) # 1, 2...
    needs = models.CharField("احتياجات خاصة", max_length=50, blank=True, null=True) # لا / نعم
    
    # بيانات ولي الأمر
    parent_national_no = EncryptedCharField("رقم ولي الأمر الشخصي", blank=True, null=True)
    parent_name = models.CharField("اسم ولي الأمر", max_length=255, blank=True, null=True)
    parent_relation = models.CharField("صلة القرابة", max_length=50, blank=True, null=True)
    parent_phone = EncryptedCharField("رقم هاتف ولي الأمر", blank=True, null=True)
    parent_email = models.EmailField("بريد ولي الأمر", blank=True, null=True)

    # حقول النظام
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    def __str__(self):
        return f"{self.name_ar} ({self.grade}/{self.section})"

    class Meta:
        managed = True
        db_table = 'students'
        verbose_name = "طالب"
        verbose_name_plural = "الطلاب"
        ordering = ['grade', 'section', 'name_ar']

    history = HistoricalRecords()

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