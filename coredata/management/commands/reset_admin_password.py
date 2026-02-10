from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Ensures the admin user exists and resets their password to 'admin'."

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        password = 'admin'
        email = 'admin@example.com'

        try:
            user = User.objects.get(username=username)
            created = False
        except User.DoesNotExist:
            user = User(username=username, email=email)
            created = True

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}' with password '{password}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully reset password for superuser '{username}' to '{password}'."))