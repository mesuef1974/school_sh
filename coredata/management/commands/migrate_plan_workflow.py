import logging
import re
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from coredata.models import Committee, OperationalPlanItems

# إعداد اللوجر
logger = logging.getLogger(__name__)

# =============================================================================
#  البيانات الأساسية للترحيل
# =============================================================================

QUALITY_COMMITTEE_MEMBERS = [
    "سلطان ناصر الهاجري", "عبد الرحمن صالح المري", "أيوب حسين القرفان",
    "عادل محمد نصر", "محمود إبراهيم سعد", "إمام محمد رشدي", "سلطان عواد",
    "بشار يوسف مزاري", "فيصل جليل الرويلي", "فليان ناصر السبيعي",
]

EXECUTOR_COMMITTEES = {
    "الإدارة المدرسية": ["سلطان ناصر الهاجري", "عبد الرحمن صالح المري", "أيوب حسين القرفان"],
    "قسم التربية الإسلامية": ["فيصل جليل الرويلي"],
    "قسم اللغة العربية": ["محمود إبراهيم سعد"],
    "قسم الرياضيات": ["محمد نادي العرامين"],
    "قسم العلوم": ["عادل محمد نصر"],
    "قسم الأحياء": ["أحمد محمد إبراهيم الجيوسي"],
    "قسم الفيزياء": ["حسن ابرهيم العربي الصافي"],
    "قسم الكيمياء": ["عطية محمود عطيه"],
    "قسم العلوم الاجتماعية": ["إمام محمد رشدي"],
    "قسم اللغة الإنجليزية": ["سلطان سعيد عبدالله عواد"],
    "قسم التربية البدنية": ["بنجر محمد بنجر الدوسري"],
    "قسم الحاسوب وتكنولوجيا المعلومات": ["محمد اسماعيل عبد الحميد السيد"],
    "قسم الفنون البصرية": ["يوسف يعقوب يونس عوض"],
    "لجنة المشاريع الالكترونية": ["فادي صالح عودات"],
    "قسم الإرشاد النفسي": ["بشار يوسف مزاري"],
    "قسم الإرشاد الاجتماعي": ["خالد جمعه السيد", "السيد عبد العال"],
    "لجنة الصحة والسلامة": ["شادي الأعرج", "أيمن الصيودي"],
    "شؤون الطلبة": ["مطلق الهاجري"],
    "السكرتارية": ["عبد الله يوسف عبد الهادي"],
    "المخزن": ["فليان ناصر السبيعي"],
}

# الخريطة النهائية: المفاتيح هنا موحدة (بدون همزات) لتطابق ناتج دالة normalize_name
JOB_TITLE_TO_COMMITTEE_MAP = {
    "مدير المدرسة": "الإدارة المدرسية",
    "النائب الاكاديمي": "الإدارة المدرسية",
    "النائب الاداري": "الإدارة المدرسية",
    "منسق التربية الاسلامية": "قسم التربية الإسلامية",
    "منسق اللغة العربية": "قسم اللغة العربية",
    "منسق الرياضيات": "قسم الرياضيات",
    "منسق العلوم": "قسم العلوم",
    "منسق الاحياء": "قسم الأحياء",
    "منسق الفيزياء": "قسم الفيزياء",
    "منسق الكيمياء": "قسم الكيمياء",
    "منسق الدراسات الاجتماعية": "قسم العلوم الاجتماعية",
    "منسق اللغة الانجليزية": "قسم اللغة الإنجليزية",
    "منسق التربية البدنية": "قسم التربية البدنية",
    "منسق تكنولوجيا المعلومات": "قسم الحاسوب وتكنولوجيا المعلومات",
    "منسق الفنون البصرية": "قسم الفنون البصرية",
    "منسق المشاريع الالكترونية": "لجنة المشاريع الالكترونية",
    "الاخصائي النفسي": "قسم الإرشاد النفسي",
    "الاخصائي الاجتماعي": "قسم الإرشاد الاجتماعي",
    "مقرر لجنة الصحة والسلامة": "لجنة الصحة والسلامة",
    "ممرض المدرسة": "لجنة الصحة والسلامة",
    "منسق شؤون الطلاب": "شؤون الطلبة",
    "سكرتير المدرسة": "السكرتارية",
    "السكرتير": "السكرتارية", # اسم بديل
    "اخصائي الانشطة المدرسية": "شؤون الطلبة",
    "المرشد الاكاديمي": "الإدارة المدرسية",
    "مقرر لجنة المراجعة الذاتية": "لجنة الجودة والمراجعة",
    "المعلمون": None,
    "مسؤول الصيانة": None,
    "مسؤول الدعم الفني": "قسم الحاسوب وتكنولوجيا المعلومات",
    "مسؤول الاذاعة": "قسم اللغة العربية",
    "مركز مصادر التعلم": "قسم اللغة العربية",
    "مسؤولو التواصل": "الإدارة المدرسية",
}


def normalize_name(name):
    if not name: return ""
    name = re.sub(r'[أإآ]', 'ا', name)
    name = re.sub(r'ى', 'ي', name)
    name = re.sub(r'ة', 'ه', name)
    name = ' '.join(name.split())
    return name


class Command(BaseCommand):
    help = "يقوم بترحيل بيانات الخطة التشغيلية من الحقول النصية إلى نظام اللجان الجديد."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_cache = list(User.objects.all())
        self.stdout.write(f"تم تحميل {len(self._user_cache)} مستخدم في الكاش.")

    def find_user_smart(self, staff_name_to_find):
        normalized_staff_name = normalize_name(staff_name_to_find)
        staff_name_parts = set(normalized_staff_name.split()[:2])

        if not staff_name_parts: return None

        for user in self._user_cache:
            user_full_name = f"{user.first_name} {user.last_name}".strip()
            if not user_full_name: continue

            normalized_user_name = normalize_name(user_full_name)
            
            if all(part in normalized_user_name for part in staff_name_parts):
                # self.stdout.write(f"  [مطابقة ناجحة] '{staff_name_to_find}' -> '{user_full_name}'")
                return user
        
        logger.warning(f"لم يتم العثور على مستخدم مطابق للموظف: {staff_name_to_find}")
        return None

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("بدء عملية الترحيل النهائية..."))

        self.setup_committees()
        self.migrate_plan_items()

        self.stdout.write(self.style.SUCCESS("تم الانتهاء من عملية الترحيل بنجاح!"))

    def setup_committees(self):
        self.stdout.write("  - الخطوة 1: إنشاء وتحديث اللجان والأعضاء...")
        
        quality_committee, _ = Committee.objects.get_or_create(name="لجنة الجودة والمراجعة")
        quality_committee.members.clear()
        for member_name in QUALITY_COMMITTEE_MEMBERS:
            user = self.find_user_smart(member_name)
            if user: quality_committee.members.add(user)

        for committee_name, members in EXECUTOR_COMMITTEES.items():
            committee, _ = Committee.objects.get_or_create(name=committee_name)
            committee.members.clear()
            for member_name in members:
                user = self.find_user_smart(member_name)
                if user: committee.members.add(user)

    def migrate_plan_items(self):
        self.stdout.write("  - الخطوة 2: ترحيل بنود الخطة التشغيلية...")
        
        items_to_migrate = OperationalPlanItems.objects.filter(executor_committee__isnull=True)
        total_items = items_to_migrate.count()
        self.stdout.write(f"  > تم العثور على {total_items} بندًا بحاجة للترحيل.")

        updated_count = 0
        skipped_count = 0

        committee_map = {c.name: c for c in Committee.objects.all()}
        quality_committee = committee_map.get("لجنة الجودة والمراجعة")

        for item in items_to_migrate:
            executor_title = item.executor.strip() if item.executor else ""
            if not executor_title:
                skipped_count += 1
                continue

            normalized_title = normalize_name(executor_title)
            committee_name = JOB_TITLE_TO_COMMITTEE_MAP.get(normalized_title)
            
            if committee_name:
                executor_committee = committee_map.get(committee_name)
                if executor_committee:
                    item.executor_committee = executor_committee
                    item.evaluator_committee = quality_committee
                    item.status = "In Progress"
                    item.save()
                    updated_count += 1
                else:
                    logger.warning(f"اللجنة '{committee_name}' غير موجودة. البند ID: {item.id}")
                    skipped_count += 1
            else:
                logger.warning(f"لم يتم العثور على لجنة مطابقة للمنصب: '{executor_title}' في البند ID: {item.id}")
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"  > تم تحديث {updated_count} بندًا بنجاح."))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"  > تم تخطي {skipped_count} بندًا (يرجى مراجعة اللوجز)."))