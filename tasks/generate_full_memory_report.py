
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.utils import timezone
from project_memory.models import (
    ProjectGoal, Technology, ArchitecturalDecision, GuidingPrinciple, 
    SwotAnalysis, ActionPlanItem, MemoryEvent
)

def generate_report():
    print("# تقرير ذاكرة منصة الشحانية الذكية")
    print(f"**تاريخ التقرير:** {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    print("\n---\n")

    # 1. الأهداف الاستراتيجية (Project Goals)
    print("## 1. الأهداف الاستراتيجية للمشروع")
    goals = ProjectGoal.objects.all().order_by('goal_type', 'name')
    if goals:
        current_type = None
        for goal in goals:
            if goal.get_goal_type_display() != current_type:
                current_type = goal.get_goal_type_display()
                print(f"\n### {current_type}")
            
            print(f"- **{goal.name}**")
            print(f"  - *الوصف*: {goal.description}")
            if goal.kpi:
                print(f"  - *KPI*: {goal.kpi}")
            if goal.measurement:
                print(f"  - *طريقة القياس*: {goal.measurement}")
    else:
        print("*لا توجد أهداف مسجلة.*")
    print("\n")

    # 2. تحليل SWOT (Swot Analysis)
    print("## 2. تحليل SWOT (نقاط القوة، الضعف، الفرص، التهديدات)")
    swots = SwotAnalysis.objects.all().order_by('category', 'title')
    if swots:
        categories = {
            'STRENGTH': 'نقاط القوة',
            'WEAKNESS': 'نقاط الضعف',
            'OPPORTUNITY': 'الفرص',
            'THREAT': 'التهديدات'
        }
        
        swot_dict = {k: [] for k in categories.keys()}
        for swot in swots:
            swot_dict[swot.category].append(swot)
            
        for cat_key, cat_name in categories.items():
            items = swot_dict.get(cat_key, [])
            if items:
                print(f"### {cat_name}")
                for item in items:
                    print(f"- **{item.title}**: {item.description or ''}")
    else:
        print("*لا يوجد تحليل SWOT مسجل.*")
    print("\n")

    # 3. المبادئ التوجيهية (Guiding Principles)
    print("## 3. المبادئ التوجيهية والحوكمة")
    principles = GuidingPrinciple.objects.all().order_by('principle_type', 'name')
    if principles:
        for principle in principles:
            print(f"- **{principle.name}** ({principle.get_principle_type_display()}): {principle.description}")
    else:
        print("*لا توجد مبادئ مسجلة.*")
    print("\n")

    # 4. المكدس التقني (Tech Stack)
    print("## 4. المكدس التقني والبنية التحتية")
    techs = Technology.objects.all().order_by('layer', 'name')
    if techs:
        layers = {}
        for tech in techs:
            if tech.layer not in layers:
                layers[tech.layer] = []
            layers[tech.layer].append(tech)
        
        for layer, tech_list in layers.items():
            print(f"### {layer}")
            for tech in tech_list:
                version_str = f" (v{tech.version})" if tech.version else ""
                print(f"- **{tech.name}**{version_str}: {tech.purpose}")
    else:
        print("*لا توجد تقنيات مسجلة.*")
    print("\n")

    # 5. سجل القرارات المعمارية (ADRs)
    print("## 5. سجل القرارات المعمارية (ADR)")
    adrs = ArchitecturalDecision.objects.all().order_by('-date')
    if adrs:
        for adr in adrs:
            icon = "✅" if adr.status == 'منفذ' else "⚠️" if adr.status == 'مقترح' else "❌"
            print(f"### {icon} {adr.adr_id}: {adr.title}")
            print(f"- **التاريخ**: {adr.date} | **الحالة**: {adr.status}")
            print(f"- **السياق**: {adr.context[:200]}..." if len(adr.context) > 200 else f"- **السياق**: {adr.context}")
            print(f"- **القرار**: {adr.decision}")
            print("")
    else:
        print("*لا توجد قرارات معمارية مسجلة.*")
    print("\n")

    # 6. خطة العمل (Action Plan)
    print("## 6. خطة العمل والأولويات")
    actions = ActionPlanItem.objects.all().order_by('-importance_score', 'status')
    if actions:
        print("| الأهمية | المهمة | الأولوية | الحالة | التعقيد |")
        print("|---|---|---|---|---|")
        for action in actions:
            status_map = {'PENDING': 'قيد الانتظار', 'IN_PROGRESS': 'جاري التنفيذ', 'DONE': 'مكتمل'}
            status_icon = {'PENDING': '⏳', 'IN_PROGRESS': '🏃', 'DONE': '✅'}
            
            status_display = f"{status_icon.get(action.status, '')} {action.get_status_display()}"
            print(f"| {action.importance_score} | {action.title} | {action.get_priority_display()} | {status_display} | {action.get_complexity_display()} |")
    else:
        print("*لا توجد خطة عمل مسجلة.*")
    print("\n")

    # 7. أحدث أحداث الذاكرة (Recent Memory Events)
    print("## 7. أحدث أحداث الذاكرة")
    events = MemoryEvent.objects.all().order_by('-timestamp')[:10]
    if events:
        for event in events:
            role = f" بواسطة {event.related_user.username}" if event.related_user else ""
            print(f"- **{event.timestamp.strftime('%Y-%m-%d')}** [{event.get_event_type_display()}]: {event.description}{role}")
    else:
        print("*لا توجد أحداث مسجلة.*")
    print("\n")

if __name__ == "__main__":
    generate_report()
