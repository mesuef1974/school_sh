import os
import django
from datetime import datetime
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from coredata.models import OperationalPlanItems
from django.db.models import Q

def run_auto_evaluate():
    print(f"--- بدء عملية التقييم الآلي: {timezone.now().strftime('%Y-%m-%d %H:%M')} ---")
    
    # 1. جلب كافة البنود التي لم يتم تقييمها بعد والتي انتهى تاريخ تنفيذها
    # ملاحظة: سنفترض أن date_range يحتوي على الشهر الأخير (مثلاً: "سبتمبر - ديسمبر 2025")
    # للتبسيط، سنبحث عن أي بند تاريخه يحتوي على سنوات سابقة أو أشهر منتهية
    
    current_year = datetime.now().year
    
    # البنود التي لم يتم إنجازها وانتهى وقتها (تبسيط: أي بند لعام 2025 ونحن في 2026)
    # أو بنود انتهت فترتها ولم يوضع لها تقييم
    expired_items = OperationalPlanItems.objects.filter(
        evaluation__in=[None, "", "لم يتم التقييم"],
        status__exclude="Completed"
    ).filter(year__lt=current_year)

    count = 0
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
    auto_note = f"تم التقييم آلياً لتجاوز الوقت المحدد ({timestamp})"

    for item in expired_items:
        item.evaluation = "غير مطابق"
        if item.evaluation_notes:
            item.evaluation_notes += f"\n{auto_note}"
        else:
            item.evaluation_notes = auto_note
        
        # تسجيل أن المقيّم هو النظام
        item.evidence_source_employee = "نظام التقييم الآلي"
        item.save()
        count += 1
        print(f"تم تصفير البند: {item.procedure_no}")

    print(f"--- اكتملت العملية. تم تقييم {count} بند آلياً كـ 'غير مطابق' ---")

if __name__ == "__main__":
    run_auto_evaluate()