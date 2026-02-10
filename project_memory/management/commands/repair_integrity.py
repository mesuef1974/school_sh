
from django.core.management.base import BaseCommand
from coredata.models import OperationalPlanItems

class Command(BaseCommand):
    help = 'Re-seals records that failed the integrity check. Use ONLY after verifying changes are legitimate.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-seal all failing records')
        parser.add_argument('--code', type=str, help='Re-seal a specific record by code')

    def handle(self, *args, **options):
        if options['all']:
            items = OperationalPlanItems.objects.filter(digital_seal__isnull=False)
        elif options['code']:
            items = OperationalPlanItems.objects.filter(code=options['code'])
        else:
            self.stderr.write(self.style.ERROR("Please specify --all or --code <record_code>"))
            return

        repaired = 0
        self.stdout.write("Starting re-sealing process...")

        for item in items:
            current_seal = item.digital_seal
            calculated_seal = item.generate_seal()
            
            if current_seal != calculated_seal:
                item.digital_seal = calculated_seal
                item.save()
                self.stdout.write(self.style.SUCCESS(f"Fixed: [{item.code}] - New seal generated."))
                repaired += 1

        if repaired > 0:
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully repaired {repaired} records."))
        else:
            self.stdout.write("No records needed repair.")
