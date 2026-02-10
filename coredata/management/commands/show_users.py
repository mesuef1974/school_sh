from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "يعرض قائمة بأسماء المستخدمين وأسمائهم الكاملة للمساعدة في عملية الترحيل."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("قائمة المستخدمين في قاعدة البيانات:"))
        self.stdout.write(self.style.WARNING("======================================="))
        
        users = User.objects.all().order_by('username')
        
        if not users.exists():
            self.stdout.write(self.style.ERROR("لم يتم العثور على أي مستخدمين في قاعدة البيانات."))
            return

        for user in users:
            full_name = f"{user.first_name} {user.last_name}".strip()
            self.stdout.write(
                f"Username: {self.style.SUCCESS(user.username):<25} | "
                f"Full Name: {self.style.NOTICE(full_name)}"
            )
            
        self.stdout.write(self.style.WARNING("======================================="))
        self.stdout.write(f"إجمالي عدد المستخدمين: {users.count()}")