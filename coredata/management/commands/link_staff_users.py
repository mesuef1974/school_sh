from django.core.management.base import BaseCommand
from coredata.models import Staff
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Link staff members to existing user accounts based on email.'

    def handle(self, *args, **options):
        # 1. الربط بناءً على البريد الإلكتروني
        staffs_no_user = Staff.objects.filter(user=None).exclude(email__in=[None, '', 'N/A'])
        linked_count = 0
        
        for staff in staffs_no_user:
            email = staff.email
            if not email: continue
            user = User.objects.filter(email__iexact=str(email).strip()).first()
            if user:
                # التأكد من أن المستخدم غير مرتبط بموظف آخر
                if not hasattr(user, 'staff'):
                    staff.user = user
                    staff.save()
                    linked_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"المستخدم {user.username} مرتبط بالفعل بموظف آخر. تخطي {staff.name}"))

        self.stdout.write(self.style.SUCCESS(f"تم ربط {linked_count} موظف بحسابات مستخدمين قائمة بناءً على البريد الإلكتروني."))

        # 2. إحصاءات نهائية
        total_staff = Staff.objects.count()
        linked_staff = Staff.objects.exclude(user=None).count()
        self.stdout.write(f"إجمالي الموظفين: {total_staff}")
        self.stdout.write(f"الموظفون المرتبطون بحسابات: {linked_staff}")
        self.stdout.write(f"الموظفون بدون حسابات: {total_staff - linked_staff}")