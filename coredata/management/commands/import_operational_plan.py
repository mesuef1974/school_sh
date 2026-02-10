import csv
import os
from django.core.management.base import BaseCommand
from coredata.models import OperationalPlanItems

class Command(BaseCommand):
    help = 'Imports operational plan items from a CSV file.'

    def handle(self, *args, **options):
        csv_path = r'D:\SULTAN_HAGRY\shaniya_django\الارشيف\Doc_School\OperationalPlanItems-2026-02-06 (1).csv'
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        self.stdout.write(self.style.WARNING("Clearing existing operational plan items..."))
        OperationalPlanItems.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Starting fresh import from {csv_path}..."))
        
        count_created = 0
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                OperationalPlanItems.objects.create(
                    year=row.get('year'),
                    rank_name=row.get('rank_name'),
                    target_no=row.get('target_no'),
                    target=row.get('target'),
                    indicator_no=row.get('indicator_no'),
                    indicator=row.get('indicator'),
                    procedure_no=row.get('procedure_no'),
                    procedure=row.get('procedure'),
                    executor=row.get('executor'),
                    date_range=row.get('date_range'),
                    follow_up=row.get('follow_up'),
                    comments=row.get('comments'),
                    evidence_type=row.get('evidence_type'),
                    evidence_source_employee=row.get('evidence_source_employee'),
                    evidence_source_file=row.get('evidence_source_file'),
                    evaluation=row.get('evaluation'),
                    evaluation_notes=row.get('evaluation_notes'),
                    status=row.get('status'),
                    digital_seal=row.get('digital_seal'),
                )
                count_created += 1

        self.stdout.write(self.style.SUCCESS(f"Import finished. Created: {count_created}"))