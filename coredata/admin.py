from django.contrib import admin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.apps import apps
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, CharField, TextField, Exists, OuterRef, Count
from django.utils.safestring import mark_safe
from django.utils.dateparse import parse_date
import json
from django.urls import path
from .models import (
    Staff, OperationalPlanItems, Committee,
    JobTitle, EvidenceFile, FilePermission,
    AcademicYear, StrategicGoal, OperationalGoal,
    Student, EvidenceDocument, GroupExtension
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'start_date', 'end_date')
    list_editable = ('is_active',)

@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = ('code', 'academic_year', 'title')
    list_filter = ('academic_year',)
    search_fields = ('title', 'code')

@admin.register(OperationalGoal)
class OperationalGoalAdmin(admin.ModelAdmin):
    list_display = ('code', 'strategic_goal', 'title')
    list_filter = ('strategic_goal__academic_year',)
    search_fields = ('title', 'code')
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter

# --- Custom Admin Index View to provide Dashboard Data ---
class CoreDataAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('activity-report/', self.admin_view(self.activity_report), name='activity_report'),
        ]
        return custom_urls + urls

    def activity_report(self, request):
        qs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')

        user_id = request.GET.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        action_flag = request.GET.get('action')
        if action_flag in {'1', '2', '3'}:
            qs = qs.filter(action_flag=int(action_flag))

        content_type_id = request.GET.get('content_type')
        if content_type_id:
            qs = qs.filter(content_type_id=content_type_id)

        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(object_repr__icontains=q) | Q(change_message__icontains=q))

        date_from = parse_date(request.GET.get('date_from', '') or '')
        if date_from:
            qs = qs.filter(action_time__date__gte=date_from)

        date_to = parse_date(request.GET.get('date_to', '') or '')
        if date_to:
            qs = qs.filter(action_time__date__lte=date_to)

        context = {
            **self.each_context(request),
            'title': 'تقرير آخر النشاطات',
            'entries': qs[:200],
            'users': User.objects.order_by('first_name', 'last_name', 'username'),
            'content_types': ContentType.objects.order_by('app_label', 'model'),
            'action_choices': [
                (ADDITION, 'إضافة'),
                (CHANGE, 'تعديل'),
                (DELETION, 'حذف'),
            ],
            'filters': {
                'user': user_id,
                'action': action_flag,
                'content_type': content_type_id,
                'q': q,
                'date_from': request.GET.get('date_from', ''),
                'date_to': request.GET.get('date_to', ''),
            }
        }
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/reports/activity.html', context)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # 1. Basic Stats
        staff_count = Staff.objects.count()
        plan_items_total = OperationalPlanItems.objects.count()
        plan_items_completed = OperationalPlanItems.objects.filter(status='Completed').count()
        student_count = Student.objects.count()
        
        extra_context.update({
            'staff_count': staff_count,
            'plan_items_total': plan_items_total,
            'plan_items_completed': plan_items_completed,
            'student_count': student_count,
        })
        
        # 2. Charts Data (Prepared for Doughnut Charts)
        def get_chart_data_local(queryset, field):
            # Define professional color palettes for Doughnut charts
            color_maps = {
                'follow_up': {
                    "تم الإنجاز": "#10b981", # Green
                    "مكتمل": "#10b981",
                    "لم يتم الإنجاز": "#ef4444", # Red
                    "مؤجل": "#f59e0b", # Amber
                    "قيد الإنجاز": "#3b82f6", # Blue
                    "جزئي": "#8b5cf6" # Purple
                },
                'evaluation': {
                    "مطابق": "#10b981",
                    "مطابق جزئي": "#f59e0b",
                    "غير مطابق": "#ef4444",
                    "مرتفع": "#10b981",
                    "متوسط": "#3b82f6",
                    "منخفض": "#ef4444"
                }
            }
            
            # Default palette if label not found
            default_colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#6366f1"]
            
            color_map = color_maps.get(field, {})
            stats = queryset.values(field).annotate(count=Count('id')).order_by('-count')
            
            labels = []
            data = []
            background_colors = []
            
            for i, item in enumerate(stats):
                label = item.get(field) or 'غير مصنف'
                count = item['count']
                labels.append(label)
                data.append(count)
                # Use mapped color or fallback to default palette
                background_colors.append(color_map.get(label, default_colors[i % len(default_colors)]))
            
            return {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': background_colors,
                    'hoverOffset': 4
                }]
            }

        qs = OperationalPlanItems.objects.all()
        extra_context['follow_up_chart_data'] = json.dumps(get_chart_data_local(qs, 'follow_up'))
        extra_context['evaluation_chart_data'] = json.dumps(get_chart_data_local(qs, 'evaluation'))
        
        # 3. Process Flow Data
        extra_context['flow_stats'] = {
            'draft': qs.filter(status='Draft').count(),
            'progress': qs.filter(status='In Progress').count(),
            'pending': qs.filter(status='Pending Review').count(),
            'completed': qs.filter(status='Completed').count(),
        }

        # 4. Student Statistics (Overview)
        student_stats = Student.objects.values('grade').annotate(count=Count('id')).order_by('grade')
        
        prep_count = 0 # 7, 8, 9
        sec_count = 0  # 10, 11, 12
        grade_counts = {str(i): 0 for i in range(7, 13)}
        
        for item in student_stats:
            grade = str(item['grade'])
            count = item['count']
            if grade in grade_counts:
                grade_counts[grade] = count
                
            if grade in ['7', '8', '9']:
                prep_count += count
            elif grade in ['10', '11', '12']:
                sec_count += count
        
        extra_context['student_stats'] = {
            'prep_total': prep_count,
            'sec_total': sec_count,
            'grades': grade_counts,
            'chart_labels': list(grade_counts.keys()),
            'chart_data': list(grade_counts.values()),
        }

        # 5. Student Sections Breakdown (Detailed 6 Charts)
        sections_raw = Student.objects.values('grade', 'section').annotate(count=Count('id')).order_by('grade', 'section')
        sections_data = {str(g): {'labels': [], 'data': []} for g in range(7, 13)}
        
        for item in sections_raw:
            g = str(item['grade'])
            if g in sections_data:
                sections_data[g]['labels'].append(f"شعبة {item['section']}")
                sections_data[g]['data'].append(item['count'])
        
        extra_context['sections_data'] = json.dumps(sections_data)
        # Pass the explicit list of grades to the template
        extra_context['grade_list'] = ['7', '8', '9', '10', '11', '12']

        extra_context['recent_activity'] = (
            LogEntry.objects.select_related('user', 'content_type')
            .order_by('-action_time')[:8]
        )

        # 6. Strategic Memory Data (Roadmap & Actions)
        try:
            from project_memory.models import ProjectGoal, ActionPlanItem, SwotAnalysis
            extra_context['roadmap_goals'] = ProjectGoal.objects.filter(goal_type='ميزة مستقبلية')
            extra_context['top_actions'] = ActionPlanItem.objects.all().order_by('-importance_score')[:5]
            extra_context['swot_items'] = SwotAnalysis.objects.all()
        except ImportError:
            pass
        
        return super().index(request, extra_context)

# Global override for the admin site
admin.site.__class__ = CoreDataAdminSite

from simple_history.admin import SimpleHistoryAdmin

# --- Custom User Admin to Display Job Title ---
class CustomUserAdmin(UserAdmin):
    list_display = ('get_full_name_custom', 'username', 'email', 'is_staff', 'get_job_title')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'staff_profile__name') # Added staff name to search

    @admin.display(description='الاسم الكامل')
    def get_full_name_custom(self, obj):
        try:
            return obj.staff_profile.name
        except:
            full_name = f"{obj.first_name} {obj.last_name}".strip()
            return full_name if full_name else obj.username

    @admin.display(description='المسمى الوظيفي')
    def get_job_title(self, obj):
        try:
            return obj.staff_profile.job_title
        except:
            return '---'

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# --- Committee Admin ---
@admin.register(Committee)
class CommitteeAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('code', 'academic_year', 'name', 'get_members_count', 'get_members_names', 'created_at')
    search_fields = ('name', 'code') # Important for autocomplete
    filter_horizontal = ('members', 'strategic_goals_link')
    list_filter = ('academic_year',)
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at', 'code')
    
    fieldsets = (
        (None, {'fields': ('code', 'academic_year', 'name', 'description')}),
        ('الأعضاء والصلاحيات', {'fields': ('members',)}),
        ('الربط الاستراتيجي', {'fields': ('strategic_goals_link',), 'description': 'ربط اللجنة بالأهداف الكبرى للمدرسة'}),
        ('بيانات النظام', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            # تخصيص عرض الاسم في قائمة الاختيار (Many-to-Many)
            kwargs["queryset"] = User.objects.all().select_related('staff_profile')
            field = super().formfield_for_manytomany(db_field, request, **kwargs)
            
            # وظيفة ذكية لتسمية الخيارات بالأسماء الحقيقية
            def label_from_instance(obj):
                try:
                    return f"{obj.staff_profile.name} ({obj.username})"
                except:
                    full_name = f"{obj.first_name} {obj.last_name}".strip()
                    return full_name if full_name else obj.username
            
            field.label_from_instance = label_from_instance
            return field
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description='عدد الأعضاء')
    def get_members_count(self, obj):
        return obj.members.count()

    @admin.display(description='الأعضاء (الأسماء)')
    def get_members_names(self, obj):
        # نحاول الحصول على الاسم من ملف الموظف (Staff) المرتبط بالمستخدم
        # إذا لم يوجد، نستخدم الاسم الأول والأخير من اليوزر
        # إذا لم يوجد، نستخدم اسم المستخدم
        members = obj.members.all()
        names = []
        for user in members:
            try:
                staff = Staff.objects.get(user=user)
                names.append(staff.name)
            except Staff.DoesNotExist:
                full_name = f"{user.first_name} {user.last_name}".strip()
                names.append(full_name if full_name else user.username)
        
        # عرض أول 5 أسماء فقط في القائمة الرئيسية مع اختصار للبقية
        display_names = names[:5]
        result = ", ".join(display_names)
        if len(names) > 5:
            result += f" ... (+{len(names) - 5})"
        return result

# --- Inlines and Helpers for Staff 360 View ---
def get_user_committees_html(user):
    if not user: return "---"
    committees = user.committees.all()
    if not committees.exists(): return "لا ينتمي لأي لجنة حالياً"
    html = '<ul style="margin: 0; padding-right: 20px;">'
    for c in committees:
        html += f'<li>{c.name} ({c.code or "بدون كود"})</li>'
    html += '</ul>'
    return html

@admin.register(Staff)
class StaffAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('name', 'job_title', 'job_number', 'account_no', 'email', 'national_no', 'user', 'created_at')
    search_fields = ('name', 'job_number', 'account_no', 'email', 'national_no', 'phone_no')
    list_filter = ('job_title', 'created_at')
    list_per_page = 50
    raw_id_fields = ('user', 'job_title')
    readonly_fields = ('created_at', 'updated_at', 'get_execution_summary', 'get_committees_display')
    
    fieldsets = (
        ('المعلومات الشخصية', {'fields': ('name', 'user', 'job_title')}),
        ('ملخص الإنجاز والنشاط', {
            'fields': ('get_execution_summary', 'get_committees_display'),
            'description': 'عرض شامل لمسؤوليات الموظف داخل المنصة'
        }),
        ('بيانات الاتصال', {'fields': ('email', 'phone_no')}),
        ('البيانات الوظيفية', {'fields': ('job_number', 'national_no', 'account_no')}),
        ('بيانات النظام', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description="ملخص الإنجاز")
    def get_execution_summary(self, obj):
        if not obj.user: return "---"
        user_committees = obj.user.committees.all()
        items = OperationalPlanItems.objects.filter(executor_committee__in=user_committees)
        total = items.count()
        completed = items.filter(status='Completed').count()
        return f"ينفذ {total} بند (تم إنجاز {completed})"

    @admin.display(description="اللجان المشترك بها")
    def get_committees_display(self, obj):
        from django.utils.safestring import mark_safe
        return mark_safe(get_user_committees_html(obj.user))

# --- Operational Plan Items Admin ---
@admin.register(OperationalPlanItems)
class OperationalPlanItemsAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    # Use our custom template for the list view
    change_list_template = 'admin/coredata/operationalplanitems/change_list.html'

    # عرض جميع الأعمدة بلا استثناء
    list_display = (
        'code', 'academic_year', 'rank_name', 'get_status_colored', 'status', 'executor', 'executor_committee', 
        'date_range', 'follow_up', 'evaluation', 
        'evidence_document', 'evaluator_committee', 'evidence_requested', 'last_review_date'
    )
    
    # جعل بعض الحقول قابلة للتعديل مباشرة من القائمة لسرعة الإنجاز
    list_editable = ('status', 'follow_up', 'evaluation')
    
    # Change status colors in list view
    def get_status_colored(self, obj):
        colors = {
            'Draft': '#6c757d',
            'In Progress': '#007bff',
            'Pending Review': '#ffc107',
            'Completed': '#28a745',
            'Returned': '#dc3545',
        }
        color = colors.get(obj.status, '#333')
        return mark_safe(f'<span style="color: white; background-color: {color}; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8em;">{obj.get_status_display()}</span>')
    get_status_colored.short_description = 'الحالة'
    get_status_colored.admin_order_field = 'status'
    
    # فلترة احترافية ومتقدمة
    list_filter = (
        'academic_year',
        'status',
        'rank_name',
        'follow_up',
        'evaluation',
        'executor_committee',
        'evaluator_committee',
        'evidence_requested',
        'evidence_type',
        'last_review_date',
        'created_at',
    )
    
    # بحث شامل في كافة نصوص البند
    search_fields = (
        'code', 'rank_name', 'target', 'indicator', 'procedure', 
        'executor', 'comments', 'evaluation_notes', 
        'evidence_source_employee', 'evidence_source_file'
    )

    readonly_fields = ('created_at', 'updated_at', 'code')
    
    # تنظيم واجهة التعديل (Fieldsets) لتكون احترافية
    fieldsets = (
        ('معلومات البند الأساسية', {
            'fields': (
                ('academic_year', 'code'),
                'rank_name', 
                ('strategic_goal_link', 'operational_goal_link'),
                'procedure'
            )
        }),
        ('التنفيذ والمتابعة', {
            'fields': ('executor', 'executor_committee', 'date_range', 'status', 'follow_up', 'comments'),
            'classes': ('wide',)
        }),
        ('الأدلة والتوثيق', {
            'fields': (
                'evidence_type', 'evidence_document', 'evidence_source_file', 'evidence_source_employee',
                'evidence_requested', 'evidence_requested_at', 'evidence_request_note'
            ),
            'description': 'اختر ملفاً من "مستودع الأدلة" الخاص بك أو اكتب المسار يدوياً في الحقل القديم.'
        }),
        ('التقييم والمراجعة', {
            'fields': ('evaluation', 'evaluator_committee', 'evaluation_notes', 'last_review_date'),
        }),
        ('بيانات النظام (للمراجعة فقط)', {
            'fields': (('target_no', 'target'), ('indicator_no', 'indicator'), 'procedure_no'),
            'classes': ('collapse',),
        }),
        ('توثيق النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    list_per_page = 20
    list_max_show_all = 100
    ordering = ('year', 'rank_name')
    
    # تحسين اختيار اللجان باستخدام البحث (autocomplete)
    autocomplete_fields = ['executor_committee', 'evaluator_committee']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "evidence_document":
            # Filter evidence documents to show only those owned by the current user
            if not request.user.is_superuser:
                kwargs["queryset"] = EvidenceDocument.objects.filter(user=request.user)
            else:
                # Superusers can see all, but maybe we want to group them or show user name
                kwargs["queryset"] = EvidenceDocument.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --- Register our new models ---
@admin.register(JobTitle)
class JobTitleAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('code', 'title', 'get_staff_count', 'created_at')
    search_fields = ('title', 'code')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='عدد الموظفين')
    def get_staff_count(self, obj):
        return obj.staff_members.count()

@admin.register(EvidenceFile)
class EvidenceFileAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('code', 'name', 'get_permissions_count', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='عدد الصلاحيات')
    def get_permissions_count(self, obj):
        return obj.permitted_jobs.count()

@admin.register(FilePermission)
class FilePermissionAdmin(ImportExportModelAdmin):
    list_display = ('job_title', 'evidence_file', 'can_view', 'created_at')
    list_filter = ('can_view', 'job_title', 'created_at')
    search_fields = ('job_title__title', 'evidence_file__name')
    raw_id_fields = ('job_title', 'evidence_file')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('name_ar', 'grade', 'section', 'national_no', 'parent_name', 'parent_phone', 'created_at')
    list_filter = ('grade', 'section', 'needs', 'created_at')
    search_fields = ('name_ar', 'name_en', 'national_no', 'parent_name', 'parent_phone', 'parent_national_no')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    fieldsets = (
        ('بيانات الطالب', {
            'fields': (('name_ar', 'name_en'), ('national_no', 'date_of_birth'), ('grade', 'section', 'needs'))
        }),
        ('بيانات ولي الأمر', {
            'fields': (('parent_name', 'parent_relation'), ('parent_phone', 'parent_email'), 'parent_national_no')
        }),
        ('بيانات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

class StaffNameFilter(admin.SimpleListFilter):
    title = 'المستخدم'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        # Only show users who have entries in EvidenceDocument
        user_ids = model_admin.model.objects.values_list('user', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids).select_related('staff_profile')
        
        options = []
        for user in users:
            name = user.username
            try:
                if hasattr(user, 'staff_profile') and user.staff_profile.name:
                    name = user.staff_profile.name
                else:
                    full_name = user.get_full_name()
                    if full_name:
                        name = full_name
            except:
                pass
            options.append((str(user.id), name))
            
        return sorted(options, key=lambda x: x[1])

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__id=self.value())
        return queryset

@admin.register(EvidenceDocument)
class EvidenceDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'evidence_type', 'get_user_full_name', 'academic_year', 'get_file_size_display', 'created_at')
    list_filter = (
        'academic_year', 
        'evidence_type', 
        ('created_at', DateRangeFilter),
        StaffNameFilter
    )
    # Comprehensive search fields for "Writing" capability in search box
    search_fields = (
        'title', 
        'description', 
        'tags', 
        'original_filename',
        'user__username', 
        'user__first_name', 
        'user__last_name',
        'user__staff_profile__name', # Search by actual Arabic name
        'evidence_type__name'
    )
    
    # Autocomplete for "Writing" capability in selection forms
    autocomplete_fields = ['user', 'evidence_type']
    
    readonly_fields = ('created_at', 'updated_at', 'original_filename', 'file_size', 'file_hash')
    
    fieldsets = (
        ('بيانات الملف', {
            'fields': ('title', 'evidence_type', 'file', 'description', 'tags')
        }),
        ('البيانات الوصفية (للقراءة فقط)', {
            'fields': ('original_filename', 'file_size', 'file_hash', 'user', 'academic_year'),
            'classes': ('collapse',)
        }),
        ('بيانات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='المستخدم (الاسم الفعلي)', ordering='user__staff_profile__name')
    def get_user_full_name(self, obj):
        try:
            return obj.user.staff_profile.name
        except:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.username

    @admin.display(description='الحجم', ordering='file_size')
    def get_file_size_display(self, obj):
        if obj.file_size:
            # Convert bytes to KB or MB
            if obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)

class GroupExtensionInline(admin.StackedInline):
    model = GroupExtension
    can_delete = False
    verbose_name_plural = 'إسناد مقيمي المحاور'
    filter_horizontal = ('axis1_evaluators', 'axis2_evaluators', 'axis3_evaluators', 'axis4_evaluators', 'axis5_evaluators', 'axis6_evaluators')
    fieldsets = (
        (None, {
            'fields': (
                ('axis1_name', 'axis1_evaluators'),
                ('axis2_name', 'axis2_evaluators'),
                ('axis3_name', 'axis3_evaluators'),
                ('axis4_name', 'axis4_evaluators'),
                ('axis5_name', 'axis5_evaluators'),
                ('axis6_name', 'axis6_evaluators'),
            )
        }),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if 'evaluators' in db_field.name:
            kwargs['queryset'] = User.objects.all().select_related('staff_profile')
            field = super().formfield_for_manytomany(db_field, request, **kwargs)
            
            def label_from_instance(obj):
                try:
                    return f"{obj.staff_profile.name} ({obj.username})"
                except:
                    full_name = f"{obj.first_name} {obj.last_name}".strip()
                    return full_name if full_name else obj.username
            
            field.label_from_instance = label_from_instance
            return field
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class MyGroupAdmin(GroupAdmin):
    def get_inlines(self, request, obj=None):
        if obj and obj.name == 'لجنة الجودة والتخطيط':
            return [GroupExtensionInline]
        return []

admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)