from django.core.management.base import BaseCommand
from project_memory.models import ArchitecturalDecision, MemoryEvent, SwotAnalysis, ProjectGoal, Technology, ActionPlanItem
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Populates project memory with recent evaluation and test enhancements.'

    def handle(self, *args, **options):
        # 1. ADR - CI/CD Upgrade
        adr1, created = ArchitecturalDecision.objects.get_or_create(
            adr_id='ADR-004',
            defaults={
                'title': 'ترقية بيئة CI/CD إلى Python 3.12',
                'date': datetime.date.today(),
                'status': 'منفذ',
                'context': 'وجود تعارض في إصدارات المكتبات (contourpy, matplotlib) مع نسخ Python القديمة في GitHub Actions.',
                'decision': 'تحديث بيئة التشغيل في CI لتتوافق مع بيئة التطوير والإنتاج (Python 3.12).',
                'justification': 'ضمان اتساق البيئات والحصول على أحدث التحسينات الأمنية استجابة لتقارير ruff ومشاكل الاعتمادية.'
            }
        )
        if created: self.stdout.write(f"Created ADR: {adr1.title}")

        # 2. ADR - Automated Testing Framework
        adr2, created = ArchitecturalDecision.objects.get_or_create(
            adr_id='ADR-005',
            defaults={
                'title': 'تأسيس إطار عمل للاختبارات الآلية (Phase 1)',
                'date': datetime.date.today(),
                'status': 'منفذ',
                'context': 'ضعف تغطية الاختبارات الآلية للعمليات الحساسة (تشفير، ختم رقمي، صلاحيات).',
                'decision': 'استخدام pytest-django وتطبيق حزمة اختبارات تغطي: التشفير، الختم الرقمي، معالجة الميديا، وRBAC.',
                'justification': 'حماية العمليات المعقدة من الأعطال المستقبلية (Regression) وضمان استقامة البيانات.'
            }
        )
        if created: self.stdout.write(f"Created ADR: {adr2.title}")

        # 3. Memory Event - Platform Evaluation
        MemoryEvent.objects.create(
            event_type='ADMIN_ACTION',
            description='إجراء تقييم شامل للمنصة وتقديم تقرير احترافي باللغة العربية والإنجليزية.',
            details={
                'focus': ['Architecture', 'Security', 'DevOps', 'Strategic Docs'],
                'outcome': 'تم تحديد نقاط القوة والضعف وتحديث خطة العمل.'
            },
            is_significant=True
        )

        # 4. Update SWOT
        SwotAnalysis.objects.get_or_create(
            category='STRENGTH',
            title='قوة الحماية والخصوصية',
            defaults={'description': 'استخدام EncryptedCharField للبيانات الحساسة وSHA-256 للختم الرقمي.'}
        )
        
        strength_test, created = SwotAnalysis.objects.get_or_create(
            category='STRENGTH',
            title='نظام اختبارات آلية للمهام المعقدة',
            defaults={'description': 'وجود تغطية اختبارية للعمليات الحرجة تضمن استدامة استقرار المنصة.'}
        )

        # 5. Action Plan Update
        action, _ = ActionPlanItem.objects.get_or_create(
            title='تعزيز الاختبارات الآلية لتغطية الحالات المعقدة',
            defaults={
                'description': 'تنفيذ حزمة اختبارات شاملة للتشفير والختم الرقمي والصلاحيات.',
                'status': 'DONE',
                'impact': 9,
                'urgency': 8,
                'priority': 'HIGH',
                'complexity': 'COMPLEX'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully updated project memory database.'))
