
from django.utils.deprecation import MiddlewareMixin
from django.db import connection

class RlsContext(MiddlewareMixin):
    """تمرير سياق RLS للمعلم بناءً على صفوفه المسموح بها.

    ملاحظة: ينبغي أن تزود كائن المستخدم بحقوله/خصائصه المعتبرة (مثل method allowed_classes_pg_array)
    ضمن بوابة الإدارة أو عبر ربط مع staff_assignments.
    """
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'allowed_classes_pg_array'):
            arr = request.user.allowed_classes_pg_array()
            with connection.cursor() as cur:
                cur.execute("SET LOCAL app.allowed_classes = %s", [arr])
