import os
import sys
import django
from datetime import date

# ضبط بيئة Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# محاولة إدراج التطبيق في الإعدادات برمجياً إذا لم يكن موجوداً
from django.conf import settings
if 'project_memory' not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS += ['project_memory']

django.setup()

from project_memory.models import ArchitecturalDecision, MemoryEvent

def update_memory():
    # 1. إضافة القرار المعماري ADR-006
    adr, created = ArchitecturalDecision.objects.get_or_create(
        adr_id='ADR-006',
        defaults={
            'title': 'استراتيجية النشر الهجين (Docker + Render)',
            'date': date.today(),
            'status': 'منفذ',
            'context': 'الحاجة لضمان اتساق البيئة البرمجية وتسهيل عملية النشر والتوسع على منصة Render مع ضمان استمرارية البيانات.',
            'decision': 'استخدام Docker كحاوية أساسية للمشروع و Render كمنصة تشغيل، مع فصل قاعدة البيانات والملفات المرفوعة عن الحاوية.',
            'justification': 'يوفر Docker بيئة معزولة تمنع مشاكل اختلاف الإعدادات، بينما يسهل Render عمليات النشر الآلي وتوفير موارد قاعدة البيانات المستقلة.'
        }
    )
    if created:
        print("✅ تم إنشاء القرار المعماري ADR-006 في قاعدة البيانات.")
    else:
        print("ℹ️ القرار المعماري ADR-006 موجود مسبقاً.")

    # 2. إضافة حدث في سجل الذاكرة
    event = MemoryEvent.objects.create(
        event_type='ADMIN_ACTION',
        description='اعتماد استراتيجية Docker + Render وأفضل ممارسات التطوير',
        details={
            'discussion_topic': 'Docker vs Render',
            'best_practices': [
                'Local dev with docker-compose',
                'Feature branching',
                'Automated migrations on Render',
                'External media storage'
            ]
        },
        is_significant=True
    )
    print(f"✅ تم تسجيل حدث الذاكرة: {event.description}")

if __name__ == "__main__":
    update_memory()