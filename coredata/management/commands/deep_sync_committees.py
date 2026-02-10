import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from coredata.models import Staff, Committee
from django.db.models import Q

def normalize(text):
    if not text: return ""
    return text.strip().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي')

def run_deep_sync():
    print("--- البدء في مزامنة اللجان والوظائف (ربط ذكي معمق) ---")
    staffs = Staff.objects.exclude(user=None).select_related('job_title')
    committees = Committee.objects.all()
    
    linked_count = 0
    
    # خريطة الربط الذكي للتخصصات
    SUBJECTS_KEYWORDS = {
        "رياضيات": ["رياضيات", "الرياضيات"],
        "عربي": ["العربية", "اللغة العربية", "عربي"],
        "انجليزي": ["الانجليزية", "اللغة الانجليزية", "اللغة الإنجليزية", "انجليزي", "الإنجليزية"],
        "شرعية": ["الشرعية", "الاسلامية", "الإسلامية", "التربية الإسلامية", "العلوم الشرعية", "شرعية"],
        "علوم": ["العلوم", "علوم", "الكيمياء", "الفيزياء", "الأحياء", "احياء", "فيزياء", "كيمياء"],
        "اجتماعية": ["الاجتماعية", "العلوم الاجتماعية", "الدراسات الاجتماعية", "تاريخ", "جغرافيا", "اجتماعيات"],
        "تكنولوجيا": ["تكنولوجيا", "الحاسوب", "المشاريع الالكترونية", "حاسب"],
        "بدنية": ["البدنية", "الرياضة", "بدنية", "رياضة"],
        "فنون": ["الفنون", "البصرية", "فنون"],
        "نفسي": ["النفسي", "نفسي"],
        "اجتماعي": ["الاجتماعي", "اجتماعي"],
        "مخزن": ["مخزن", "مستودع", "الموارد"],
        "اداري": ["إداري", "اداري", "مدير", "النائب", "سكرتير"],
    }

    for s in staffs:
        if not s.job_title: continue
        s_title_norm = normalize(s.job_title.title)
        
        # تحديد الكلمات المفتاحية لمادة الموظف
        relevant_subjects = []
        for subject, keywords in SUBJECTS_KEYWORDS.items():
            if any(normalize(kw) in s_title_norm for kw in keywords):
                relevant_subjects.append(subject)
        
        for c in committees:
            c_name_norm = normalize(c.name)
            is_match = False
            
            # 1. المطابقة المباشرة أو الجزئية
            if s_title_norm == c_name_norm or s_title_norm in c_name_norm or c_name_norm in s_title_norm:
                is_match = True
            
            # 2. مطابقة التخصص مع "منسق" أو "معلم" في اسم اللجنة
            if not is_match:
                for sub in relevant_subjects:
                    sub_keywords = SUBJECTS_KEYWORDS[sub]
                    if any(normalize(kw) in c_name_norm for kw in sub_keywords):
                        # إذا كان الموظف له علاقة بمادة اللجنة، نربطه
                        is_match = True
                        break
            
            if is_match:
                # التأكد من عدم التكرار في الطباعة
                if s.user not in c.members.all():
                    c.members.add(s.user)
                    linked_count += 1
                    print(f"تم ربط [{s.name}] ({s.job_title.title}) باللجنة [{c.name}]")

    print(f"\n--- تم الانتهاء. إجمالي عمليات الربط الجديدة الناجحة: {linked_count} ---")

if __name__ == "__main__":
    run_deep_sync()