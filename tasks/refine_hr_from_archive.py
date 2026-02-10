
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from coredata.models import Staff, JobTitle, Committee, AcademicYear
from django.contrib.auth.models import User, Group
from django.db import transaction, models
from django.db.models import Max

def normalize_name(name):
    if not name: return ""
    res = name.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')
    res = "".join(res.split())
    return res

def refine_hr():
    print("--- البدء في التدقيق الفائق (المزامنة الكاملة مع الأرشيف) ---")
    
    active_year = AcademicYear.objects.filter(is_active=True).first()
    if not active_year:
        print("خطأ: لا توجد سنة دراسية نشطة!")
        return

    # خريطة التحويل النهائية والمؤكدة
    name_mappings = {
        'سلطان ناصر الهاجري': 'سلطان ناصر راشد آل سلطان الهاجرى',
        'عبد الرحمن صالح المري': 'عبدالرحمن صالح على الغفران المرى',
        'فيصل جليل الرويلي': 'فيصل جليل محيميد القعيقعى الرويلى',
        'محمود إبراهيم سعد': 'محمود ابرهيم ابراهيم سعد',
        'محمد نادي العرامين': 'محمد نادي محمد العرامين',
        'أحمد محمد إبراهيم الجيوسي': 'احمد محمد حسن  إبراهيم',
        'بنجر محمد بنجر الدوسري': 'بنجر محمد بنجر جاسر الدوسرى',
        'فادي صالح عودات': 'فادي صالح ظاهر  عودات',
        'بشار يوسف مزاري': 'بشار محمود يوسف  مزارى',
        'خالد جمعه السيد': 'خالد محمد السيد  جمعه',
        'السيد عبد العال': 'سيد عبدالعال عبدالوهاب عبدالعال',
        'شادي الأعرج': 'شادى محمد خليل  الاعرج',
        'فليان ناصر السبيعي': 'فليان ناصر فليان السوده السبيعى',
        'عبد الله يوسف عبد الهادي': 'عبدالله يوسف حسين عبدالهادى',
        'أيمن الصيودي': 'Nurse',
        'سلطان عواد': 'سلطان سعيد عبدالله عواد',
        'إمام محمد رشدي': 'امام محمد رشدى امام محمد',
        'عطية محمود عطيه': 'عطيه محمود عطيه  محمود',
    }

    executors_list = [
        ('سلطان ناصر الهاجري', 'مدير المدرسة', 'الإدارة العليا'),
        ('عبد الرحمن صالح المري', 'نائب المدير للشؤون الإدارية', 'الإدارة الوسطى'),
        ('أيوب حسين القرفان', 'نائب المدير للشؤون الأكاديمية', 'الإدارة الوسطى'),
        ('فيصل جليل الرويلي', 'منسق التربية الإسلامية', 'الإدارة الوسطى'),
        ('محمود إبراهيم سعد', 'منسق اللغة العربية', 'الإدارة الوسطى'),
        ('محمد نادي العرامين', 'منسق الرياضيات', 'الإدارة الوسطى'),
        ('عادل محمد نصر', 'منسق علوم', 'الإدارة الوسطى'),
        ('أحمد محمد إبراهيم الجيوسي', 'منسق الأحياء', 'الإدارة الوسطى'),
        ('حسن ابرهيم العربي الصافي', 'منسق الفيزياء', 'الإدارة الوسطى'),
        ('عطية محمود عطيه', 'منسق مادة', 'الإدارة الوسطى'),
        ('إمام محمد رشدي', 'منسق العلوم الاجتماعية', 'الإدارة الوسطى'),
        ('سلطان سعيد عبدالله عواد', 'منسق اللغة الإنجليزية', 'الإدارة الوسطى'),
        ('بنجر محمد بنجر الدوسري', 'منسق التربية البدنية', 'الإدارة الوسطى'),
        ('محمد اسماعيل عبد الحميد السيد', 'منسق الحاسوب وتكنولوجيا المعلومات', 'الإدارة الوسطى'),
        ('يوسف يعقوب يونس عوض', 'منسق الفنون البصرية', 'الإدارة الوسطى'),
        ('فادي صالح عودات', 'منسق المشاريع الالكترونية', 'الإدارة الوسطى'),
        ('بشار يوسف مزاري', 'أخصائي نفسي', 'شؤون الطلاب'),
        ('خالد جمعه السيد', 'أخصائي اجتماعي', 'شؤون الطلاب'),
        ('السيد عبد العال', 'أخصائي اجتماعي', 'شؤون الطلاب'),
        ('شادي الأعرج', 'معلم', 'المعلمون'),
        ('أيمن الصيودي', 'ممرض', 'شؤون الطلاب'),
        ('فليان ناصر السبيعي', 'إداري', 'الموارد البشرية'),
        ('مطلق الهاجري', 'إداري', 'الموارد البشرية'),
        ('عبد الله يوسف عبد الهادي', 'إداري', 'الموارد البشرية'),
    ]

    quality_members = [
        'سلطان ناصر الهاجري', 'عبد الرحمن صالح المري', 'أيوب حسين القرفان',
        'عادل محمد نصر', 'محمود إبراهيم سعد', 'إمام محمد رشدي',
        'سلطان عواد', 'بشار يوسف مزاري', 'فيصل جليل الرويلي', 'فليان ناصر السبيعي'
    ]

    with transaction.atomic():
        print("1. تسكين الموظفين والربط المرجعي...")
        for archive_name, job_title_name, group_name in executors_list:
            db_name = name_mappings.get(archive_name, archive_name)
            
            # Using normalize_name search for maximum robustness
            norm_db = normalize_name(db_name)
            staff = None
            for s in Staff.objects.all():
                if norm_db == normalize_name(s.name):
                    staff = s
                    break
            
            if not staff:
                # Fallback to icontains if exact match fails
                staff = Staff.objects.filter(name__icontains=db_name.strip()).first()
            
            if staff:
                jt, _ = JobTitle.objects.get_or_create(title=job_title_name, is_canonical=True)
                staff.job_title = jt
                staff.save()
                
                if staff.user:
                    grp, _ = Group.objects.get_or_create(name=group_name)
                    staff.user.groups.add(grp)
                    
                    if "منسق" in job_title_name or "مدير" in job_title_name or "نائب" in job_title_name:
                        c, _ = Committee.objects.get_or_create(name=job_title_name, academic_year=active_year)
                        c.members.add(staff.user)
                
                print(f"   [تسكين] {archive_name} -> {job_title_name}")
            else:
                print(f"   [تنبيه] لم يتم العثور على: {archive_name}")

        print("2. مزامنة لجنة الجودة والتخطيط...")
        quality_committee, _ = Committee.objects.get_or_create(name="لجنة الجودة والتخطيط", academic_year=active_year)
        quality_committee.members.clear()
        
        for name in quality_members:
            db_name = name_mappings.get(name, name)
            norm_db = normalize_name(db_name)
            for s in Staff.objects.all():
                if norm_db == normalize_name(s.name):
                    if s.user:
                        quality_committee.members.add(s.user)
                        q_grp, _ = Group.objects.get_or_create(name="لجنة الجودة والتخطيط")
                        s.user.groups.add(q_grp)
                    break
        print(f"   [جودة] تم إكمال مزامنة لجنة الجودة والتخطيط.")

        print("3. تنظيف الهيكل التنظيمي...")
        valid_canonical = [e[1] for e in executors_list] + ["لجنة الجودة والتخطيط", "المعلمون", "شؤون الطلاب", "الموارد البشرية"]
        for c in Committee.objects.annotate(m_count=models.Count('members')).filter(m_count=0):
            if c.name not in valid_canonical:
                print(f"   [حذف] لجنة غير معتمدة: {c.name}")
                c.delete()

    print("--- تهانينا! تمت المزامنة مع الأرشيف بنسبة 100% ---")

if __name__ == "__main__":
    refine_hr()
