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

def run_sync():
    print("--- البدء في مزامنة اللجان والوظائف (ربط شامل) ---")
    staffs = Staff.objects.exclude(user=None).select_related('job_title')
    committees = Committee.objects.all()
    
    linked_count = 0
    
    for s in staffs:
        if not s.job_title: continue
        s_title_norm = normalize(s.job_title.title)
        
        for c in committees:
            c_name_norm = normalize(c.name)
            
            # الربط إذا كان المسمى الوظيفي يطابق اسم اللجنة أو جزء منها
            # أو إذا كانت اللجنة تحتوي على كلمة "منسق" + تخصص الموظف
            is_match = False
            
            if s_title_norm == c_name_norm:
                is_match = True
            elif s_title_norm in c_name_norm:
                is_match = True
            elif c_name_norm in s_title_norm:
                is_match = True
            
            # منطق خاص للمنسقين والمعلمين
            if not is_match:
                if "منسق" in c_name_norm:
                    # استخراج التخصص من اسم اللجنة (مثلا "منسق الرياضيات" -> "الرياضيات")
                    specialty = c_name_norm.replace("منسق", "").strip()
                    if specialty and specialty in s_title_norm:
                        is_match = True
            
            if is_match:
                c.members.add(s.user)
                linked_count += 1
                print(f"تم ربط الموظف [{s.name}] باللجنة [{c.name}]")

    print(f"\n--- تم الانتهاء. إجمالي عمليات الربط الناجحة: {linked_count} ---")

if __name__ == "__main__":
    run_sync()