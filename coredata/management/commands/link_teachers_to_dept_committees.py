from coredata.models import Staff, Committee
from django.contrib.auth.models import User
from django.db.models import Q

def run():
    print("--- البدء في ضم المعلمين والمدرسين إلى لجان منسقيهم آلياً ---")
    
    # 1. تعريف خريطة المواد والكلمات المفتاحية
    SUBJECTS_MAP = {
        "الرياضيات": ["رياضيات", "الرياضيات"],
        "اللغة العربية": ["العربية", "اللغة العربية"],
        "اللغة الانجليزية": ["الإنجليزية", "الانجليزية", "اللغة الانجليزية", "اللغة الإنجليزية"],
        "التربية الإسلامية": ["الإسلامية", "الاسلامية", "التربية الإسلامية", "العلوم الشرعية"],
        "العلوم": ["العلوم", "الكيمياء", "الفيزياء", "الأحياء"],
        "العلوم الاجتماعية": ["الاجتماعية", "العلوم الاجتماعية", "الدراسات الاجتماعية"],
        "تكنولوجيا المعلومات": ["تكنولوجيا", "الحاسوب"],
        "التربية البدنية": ["البدنية", "الرياضة"],
        "الفنون البصرية": ["الفنون", "البصرية"],
    }

    # 2. جلب كافة الموظفين الذين لديهم حساب مستخدم
    staffs = Staff.objects.exclude(user=None).select_related('job_title')
    
    linked_count = 0
    
    for staff in staffs:
        if not staff.job_title:
            continue
            
        job_title_text = staff.job_title.title
        
        # البحث عن المادة المناسبة للموظف
        target_subject = None
        for subject_name, keywords in SUBJECTS_MAP.items():
            if any(kw in job_title_text for kw in keywords):
                target_subject = subject_name
                break
        
        if target_subject:
            # البحث عن لجنة "المنسق" لهذه المادة
            # نبحث عن لجنة تحتوي على كلمة "منسق" واسم "المادة"
            coordinator_committee = Committee.objects.filter(
                Q(name__icontains="منسق") & Q(name__icontains=target_subject)
            ).first()
            
            if coordinator_committee:
                coordinator_committee.members.add(staff.user)
                print(f"تم ضم [{staff.name}] ({job_title_text}) إلى لجنة [{coordinator_committee.name}]")
                linked_count += 1
            else:
                # إذا لم نجد لجنة باسم "منسق"، نبحث عن أي لجنة تابعة للمادة
                dept_committee = Committee.objects.filter(name__icontains=target_subject).first()
                if dept_committee:
                    dept_committee.members.add(staff.user)
                    print(f"تم ضم [{staff.name}] إلى لجنة القسم [{dept_committee.name}]")
                    linked_count += 1

    print(f"\n--- اكتملت العملية. تم ضم {linked_count} موظفاً إلى لجان تخصصاتهم بنجاح ---")

if __name__ == "__main__":
    run()