from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """
    يعرض لوحة القيادة الرئيسية.
    """
    # في المستقبل، يمكننا إضافة سياق هنا مثل الإحصائيات والرسوم البيانية
    context = {
        'welcome_message': 'مرحباً بك في منصة مدرسة الشحانية الذكية'
    }
    return render(request, 'dashboard/main.html', context)