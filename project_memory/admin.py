from django.contrib import admin
from .models import ArchitecturalDecision, ProjectGoal, Technology, GuidingPrinciple, MemoryEvent, SwotAnalysis, ActionPlanItem

# All models are now registered to the default admin site.
# The `site=site` argument has been removed.

@admin.register(ArchitecturalDecision)
class ArchitecturalDecisionAdmin(admin.ModelAdmin):
    list_display = ('adr_id', 'title', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('adr_id', 'title', 'context', 'decision', 'justification')
    list_per_page = 20
    fieldsets = (
        (None, {'fields': ('adr_id', 'title', 'date', 'status')}),
        ('تفاصيل القرار', {'classes': ('collapse',), 'fields': ('context', 'decision', 'justification')}),
    )

@admin.register(ProjectGoal)
class ProjectGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal_type', 'kpi')
    list_filter = ('goal_type',)
    search_fields = ('name', 'description', 'kpi')

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'layer', 'version')
    list_filter = ('layer',)
    search_fields = ('name', 'purpose')

@admin.register(GuidingPrinciple)
class GuidingPrincipleAdmin(admin.ModelAdmin):
    list_display = ('name', 'principle_type')
    list_filter = ('principle_type',)
    search_fields = ('name', 'description')

@admin.register(MemoryEvent)
class MemoryEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'description', 'related_user', 'is_significant')
    list_filter = ('event_type', 'is_significant', 'timestamp')
    search_fields = ('description', 'details')
    list_per_page = 50
    
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
    
    readonly_fields = ('timestamp', 'event_type', 'description', 'details', 'related_user')
    fields = ('timestamp', 'event_type', 'description', 'details', 'related_user', 'is_significant')

@admin.register(SwotAnalysis)
class SwotAnalysisAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'description')
    ordering = ('category', 'title')

@admin.register(ActionPlanItem)
class ActionPlanItemAdmin(admin.ModelAdmin):
    list_display = ('importance_score', 'title', 'priority', 'status', 'complexity', 'estimated_duration_hours', 'planned_start')
    list_filter = ('priority', 'status', 'complexity', 'planned_start')
    search_fields = ('title', 'description')
    filter_horizontal = ('related_swot',)
    readonly_fields = ('importance_score', 'created_at', 'updated_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'description', 'related_goal')
        }),
        ('الوزن الاستراتيجي (المعادلة)', {
            'fields': (('impact', 'urgency'), 'importance_score'),
            'description': 'مؤشر الأهمية = الأثر الاستراتيجي × درجة الاستعجال'
        }),
        ('إدارة المشروع والوقت', {
            'fields': (('priority', 'status', 'complexity'), ('planned_start', 'estimated_duration_hours'))
        }),
        ('روابط إضافية', {
            'fields': ('related_swot',),
            'classes': ('collapse',)
        }),
    )