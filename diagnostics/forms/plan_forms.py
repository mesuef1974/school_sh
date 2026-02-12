from django import forms
from django.db.models import Q
from ..models import OperationalPlanItems, Staff, EvidenceFile, EvidenceDocument

class PlanItemForm(forms.ModelForm):
    class Meta:
        model = OperationalPlanItems
        fields = '__all__'
        widgets = {
            'target': forms.Textarea(attrs={'rows':3}),
            'indicator': forms.Textarea(attrs={'rows':3}),
            'procedure': forms.Textarea(attrs={'rows':3}),
            'comments': forms.Textarea(attrs={'rows':2}),
            'evaluation_notes': forms.Textarea(attrs={'rows':2}),
        }

class PlanItemExecutionForm(forms.ModelForm):
    """
    نموذج مخصص لتحديث بيانات التنفيذ.
    """
    
    # تعريف الخيارات
    STATUS_CHOICES = [
        ('In Progress', 'جاري التنفيذ'),
        ('Pending Review', 'بانتظار المراجعة'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="حالة البند",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    FOLLOW_UP_CHOICES = [
        ('', 'اختر الحالة...'),
        ('تم الإنجاز', 'تم الإنجاز'),
        ('مؤجل', 'مؤجل'),
        ('لم يتم الإنجاز', 'لم يتم الإنجاز'),
        ('قيد الإنجاز', 'قيد الإنجاز'),
    ]

    EVIDENCE_TYPE_CHOICES = [
        ('', 'اختر النوع...'),
        ('كمي', 'كمي'),
        ('وصفي', 'وصفي'),
        ('كمي/وصفي', 'كمي/وصفي'),
    ]

    # تعريف الحقول مع الخيارات
    follow_up = forms.ChoiceField(
        choices=FOLLOW_UP_CHOICES,
        required=False,
        label="حالة المتابعة",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    evidence_type = forms.ChoiceField(
        choices=EVIDENCE_TYPE_CHOICES,
        required=False,
        label="نوع الدليل",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # نستخدم ModelChoiceField لربطه بجدول الملفات
    evidence_document = forms.ModelChoiceField(
        queryset=EvidenceDocument.objects.none(), # Will be filtered in __init__
        required=False,
        label="ارفاق دليل من المستودع (خزنة ملفاتي)",
        widget=forms.Select(attrs={'class': 'form-control select-gold'}),
        empty_label="--- اختر ملفاً من مستودع الأدلة ---"
    )

    evidence_source_file = forms.ModelChoiceField(
        queryset=EvidenceFile.objects.all(), # Start with all, then filter
        required=False,
        label="موقع الدليل (الملف)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- اختر ملف الدليل ---"
    )

    class Meta:
        model = OperationalPlanItems
        fields = [
            'status',
            'follow_up',
            'evidence_type',
            'evidence_source_file',
            'evidence_document',
            'comments',
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'اكتب ملاحظات التنفيذ هنا...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PlanItemExecutionForm, self).__init__(*args, **kwargs)

        # --- DEBUG PRINT FOR THE AGENT ---
        # print(f"DEBUG: PlanItemExecutionForm initialized for user: {self.user}")

        # --- 1. Get User's Allowed Files ---
        allowed_files_names = []
        staff_member = None
        
        # Determine current item area (Rank Name)
        
        # Default behavior: If user is authenticated, show all files for now
        # because the specific FilePermission table has been removed.
        if self.user and self.user.is_authenticated:
            allowed_files_qs = EvidenceFile.objects.all()
        else:
            allowed_files_qs = EvidenceFile.objects.none()

        # --- LAST RESORT FALLBACK ---
        # If still empty, it's possible the user's staff profile is not linked or permissions are missing.
        # As a safety measure to prevent "Empty Dropdown", if the user is authenticated, 
        # let's show all evidence files for now, but ONLY if the strict filtering failed.
        if not allowed_files_qs.exists() and self.user and self.user.is_authenticated:
            allowed_files_qs = EvidenceFile.objects.all()

        # --- 2. Get the Saved File (if it exists) ---
        saved_file_qs = EvidenceFile.objects.none()
        saved_file_name = self.instance.evidence_source_file
        if saved_file_name:
            saved_file_qs = EvidenceFile.objects.filter(name__iexact=saved_file_name.strip())

        # --- 3. Combine them and set the queryset ---
        # IMPORTANT: Use .distinct() and ensure we handle the case where allowed_files_qs might be empty
        final_qs = (allowed_files_qs | saved_file_qs).distinct()
        
        # If final_qs is empty and the user is a superuser, show all files
        if not final_qs.exists() and self.user and self.user.is_superuser:
            final_qs = EvidenceFile.objects.all()

        self.fields['evidence_source_file'].queryset = final_qs

        # --- 5. Filter EvidenceDocument (Vault) for the current user ---
        if self.user:
            if self.user.is_superuser:
                self.fields['evidence_document'].queryset = EvidenceDocument.objects.all()
            else:
                self.fields['evidence_document'].queryset = EvidenceDocument.objects.filter(user=self.user)

        # --- 6. Set Initial Values ---
        if saved_file_name:
            initial_obj = self.fields['evidence_source_file'].queryset.filter(name__iexact=saved_file_name.strip()).first()
            if initial_obj:
                self.fields['evidence_source_file'].initial = initial_obj

    def clean_comments(self):
        """
        Append timestamp to comments if they have changed.
        """
        comments = self.cleaned_data.get('comments')
        old_comments = self.instance.comments
        
        if comments and comments != old_comments:
            from django.utils import timezone
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            # If it doesn't already end with this timestamp (to avoid double appending if called multiple times)
            if not comments.strip().endswith(f"({timestamp})"):
                return f"{comments.strip()} ({timestamp})"
        return comments

    def clean_evidence_source_file(self):
        file_obj = self.cleaned_data.get('evidence_source_file')
        return file_obj.name if file_obj else None


class EvidenceUploadForm(forms.ModelForm):
    """
    نموذج لرفع دليل جديد مباشرة وربطه ببند الخطة.
    """
    file = forms.FileField(
        label="اختيار الملف من الجهاز",
        widget=forms.FileInput(attrs={'class': 'form-control gold-border', 'accept': '.pdf,.jpg,.jpeg,.png,.docx'})
    )

    class Meta:
        model = EvidenceDocument
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control gold-border', 'placeholder': 'عنوان الدليل (مثلاً: سجل حضور شهر فبراير)'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control gold-border', 'placeholder': 'وصف مختصر للدليل...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True


class PlanItemEvaluationForm(forms.ModelForm):
    """
    نموذج مخصص لتقييم الإجراء.
    """
    EVALUATION_CHOICES = [
        ('', '--- اختر التقييم ---'),
        ('متحقق', 'متحقق'),
        ('متحقق جزئيا', 'متحقق جزئياً'),
        ('غير متحقق', 'غير متحقق'),
    ]
    
    STATUS_CHOICES = [
        ('In Progress', 'جاري التنفيذ'),
        ('Pending Review', 'بانتظار المراجعة'),
        ('Completed', 'اعتماد النهوض (مكتمل)'),
        ('Returned', 'إعادة للمنفذ (مرفوض)'),
    ]

    evaluation = forms.ChoiceField(
        choices=EVALUATION_CHOICES,
        required=False,
        label="التقييم",
        widget=forms.Select(attrs={'class': 'form-control gold-border'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="قرار اللجنة",
        widget=forms.Select(attrs={'class': 'form-control gold-border'})
    )

    class Meta:
        model = OperationalPlanItems
        fields = [
            'status',
            'evaluation',
            'evidence_source_employee',
            'evaluation_notes',
            'evidence_requested',
            'evidence_request_note',
        ]
        widgets = {
            'evaluation_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control gold-border', 'placeholder': 'ملاحظات لجنة المراجعة...'}),
            'evidence_source_employee': forms.TextInput(attrs={'class': 'form-control gold-border', 'placeholder': 'اسم المقيّم'}),
            'evidence_request_note': forms.Textarea(attrs={'rows': 2, 'class': 'form-control gold-border', 'placeholder': 'سبب طلب الدليل...'}),
            'evidence_requested': forms.CheckboxInput(attrs={'class': 'checkbox-gold'}),
        }