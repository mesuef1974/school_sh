
from django.core.management.base import BaseCommand
from coredata.models import OperationalPlanItems

class Command(BaseCommand):
    help = 'Verifies the integrity of records with digital seals (SHA-256).'

    def handle(self, *args, **options):
        items = OperationalPlanItems.objects.filter(digital_seal__isnull=False)
        total = items.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING("No sealed records found to verify."))
            return

        verified = 0
        tampered = []

        self.stdout.write(f"Verifying {total} sealed records...")

        for item in items:
            calculated_seal = item.generate_seal()
            if calculated_seal == item.digital_seal:
                verified += 1
            else:
                tampered.append((item, calculated_seal))

        # Output Results
        self.stdout.write("\n" + "="*40)
        self.stdout.write(f"Verification Results:")
        self.stdout.write(f"Total Checked: {total}")
        self.stdout.write(self.style.SUCCESS(f"Verified: {verified}"))
        
        if tampered:
            self.stdout.write(self.style.ERROR(f"Tampered/Modified: {len(tampered)}"))
            self.stdout.write("\nDetailed List of Compromised Records:")
            for item, calc_seal in tampered:
                self.stdout.write(self.style.ERROR(f"- [{item.code}] {item.procedure[:50]}..."))
                self.stdout.write(f"  Stored Seal: {item.digital_seal[:16]}...")
                self.stdout.write(f"  Current Seal: {calc_seal[:16]}...")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All records passed integrity check. No unauthorized modifications detected."))
        self.stdout.write("="*40 + "\n")
