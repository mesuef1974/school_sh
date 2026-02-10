from django.db import models
from django.contrib.auth.models import User

class ArchitecturalDecision(models.Model):
    STATUS_CHOICES = [('منفذ', 'منفذ'), ('مقترح', 'مقترح'), ('ملغي', 'ملغي')]
    adr_id = models.CharField("رقم القرار", max_length=10, unique=True)
    title = models.CharField("العنوان", max_length=255)
    date = models.DateField("التاريخ")
    status = models.CharField("الحالة", max_length=50, choices=STATUS_CHOICES, default='مقترح')
    context = models.TextField("السياق", help_text="ما هي المشكلة أو السياق الذي أدى إلى هذا القرار؟")
    decision = models.TextField("القرار", help_text="ما هو القرار التقني الذي تم اتخاذه؟")
    justification = models.TextField("المبررات", help_text="لماذا تم اتخاذ هذا القرار؟ ما هي البدائل التي تم النظر فيها؟")

    def __str__(self):
        return f"{self.adr_id}: {self.title}"

    class Meta:
        verbose_name = "قرار معماري"
        verbose_name_plural = "سجل القرارات المعمارية"
        ordering = ['-date', '-adr_id']

class ProjectGoal(models.Model):
    GOAL_TYPE_CHOICES = [('استراتيجي', 'استراتيجي'), ('قصير المدى', 'قصير المدى'), ('ميزة مستقبلية', 'ميزة مستقبلية')]
    name = models.CharField("الهدف", max_length=255, unique=True, db_index=True)
    description = models.TextField("الوصف")
    goal_type = models.CharField("نوع الهدف", max_length=50, choices=GOAL_TYPE_CHOICES, db_index=True)
    kpi = models.CharField("مؤشر الأداء الرئيسي (KPI)", max_length=255, blank=True, null=True)
    measurement = models.CharField("كيفية القياس", max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"[{self.get_goal_type_display()}] {self.name}"

    class Meta:
        verbose_name = "هدف المشروع"
        verbose_name_plural = "أهداف المشروع"

class Technology(models.Model):
    name = models.CharField("التقنية", max_length=100, unique=True, db_index=True)
    version = models.CharField("الإصدار", max_length=50, blank=True, null=True)
    layer = models.CharField("الطبقة", max_length=100, db_index=True)
    purpose = models.TextField("سبب الاختيار")

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.version})" if self.version else self.name

    class Meta:
        verbose_name = "تقنية مستخدمة"
        verbose_name_plural = "المكدس التقني"

class GuidingPrinciple(models.Model):
    PRINCIPLE_TYPE_CHOICES = [('هندسي', 'هندسي'), ('حوكمة', 'حوكمة')]
    name = models.CharField("المبدأ", max_length=255, unique=True)
    description = models.TextField("الوصف")
    principle_type = models.CharField("نوع المبدأ", max_length=50, choices=PRINCIPLE_TYPE_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مبدأ توجيهي"
        verbose_name_plural = "المبادئ والحوكمة"

class MemoryEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('CODE_CHANGE', 'تغيير في الكود'),
        ('MIGRATION', 'تطبيق هجرة'),
        ('DEPENDENCY', 'تغيير في المكتبات'),
        ('ADMIN_ACTION', 'إجراء إداري'),
        ('USER_COMMENT', 'تعليق مستخدم'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="التوقيت")
    event_type = models.CharField("نوع الحدث", max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.TextField("الوصف")
    details = models.JSONField("تفاصيل", blank=True, null=True)
    is_significant = models.BooleanField("حدث هام؟", default=False, help_text="هل يجب أن يتحول هذا الحدث إلى قرار معماري (ADR)؟")
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المستخدم المرتبط")

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.description[:50]}"

    class Meta:
        verbose_name = "حدث في الذاكرة"
        verbose_name_plural = "سجل أحداث الذاكرة"
        ordering = ['-timestamp']

class SwotAnalysis(models.Model):
    CATEGORY_CHOICES = [
        ('STRENGTH', 'نقطة قوة'),
        ('WEAKNESS', 'نقطة ضعف'),
        ('OPPORTUNITY', 'فرصة'),
        ('THREAT', 'تهديد'),
    ]
    category = models.CharField("التصنيف", max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    title = models.CharField("العنوان", max_length=255, db_index=True)
    description = models.TextField("الوصف", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    class Meta:
        verbose_name = "عنصر SWOT"
        verbose_name_plural = "تحليل SWOT"

class ActionPlanItem(models.Model):
    PRIORITY_CHOICES = [('HIGH', 'عالية'), ('MEDIUM', 'متوسطة'), ('LOW', 'منخفضة')]
    STATUS_CHOICES = [('PENDING', 'قيد الانتظار'), ('IN_PROGRESS', 'جاري التنفيذ'), ('DONE', 'مكتمل')]
    COMPLEXITY_CHOICES = [('SIMPLE', 'بسيط'), ('MEDIUM', 'متوسط'), ('COMPLEX', 'مركب')]
    
    title = models.CharField("الإجراء", max_length=255, db_index=True)
    description = models.TextField("التفاصيل", blank=True, null=True)
    related_goal = models.ForeignKey(ProjectGoal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الهدف المرتبط", related_name="actions")
    
    # Strategic Metadata
    impact = models.IntegerField("الأثر الاستراتيجي (1-10)", default=5)
    urgency = models.IntegerField("درجة الاستعجال (1-10)", default=5)
    importance_score = models.IntegerField("مؤشر الأهمية", editable=False, default=0)
    
    # Project Management Metadata
    priority = models.CharField("الأولوية", max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', db_index=True)
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    complexity = models.CharField("التعقيد", max_length=20, choices=COMPLEXITY_CHOICES, default='MEDIUM')
    planned_start = models.DateField("تاريخ البدء المخطط", blank=True, null=True)
    estimated_duration_hours = models.DecimalField("المدة التقديرية (ساعة)", max_length=10, max_digits=5, decimal_places=1, default=0)
    
    related_swot = models.ManyToManyField(SwotAnalysis, blank=True, verbose_name="مرتبط بـ SWOT")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate Importance Score: Impact x Urgency
        self.importance_score = self.impact * self.urgency
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.importance_score}] {self.title}"

    class Meta:
        verbose_name = "إجراء تنفيذي"
        verbose_name_plural = "خطة العمل"
        ordering = ['-importance_score', '-priority']