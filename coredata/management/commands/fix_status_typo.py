from django.core.management.base import BaseCommand
from coredata.models import OperationalPlanItems

class Command(BaseCommand):
    help = 'Fixes typos in status fields (adds Hamza to "لم يتم الانجاز")'

    def handle(self, *args, **options):
        # Fix follow_up field
        updated_count_follow_up = OperationalPlanItems.objects.filter(follow_up='لم يتم الانجاز').update(follow_up='لم يتم الإنجاز')
        
        # Fix evaluation field (just in case)
        updated_count_evaluation = OperationalPlanItems.objects.filter(evaluation='لم يتم الانجاز').update(evaluation='لم يتم الإنجاز')

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count_follow_up} records in follow_up field.'))
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count_evaluation} records in evaluation field.'))