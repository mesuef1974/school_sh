import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from project_memory.models import GuidingPrinciple

class Command(BaseCommand):
    help = 'Imports Guiding Principles and Governance Protocols from the HTML memory file.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'memory', '07_Protocol_And_Governance.html')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found at: {file_path}'))
            return

        self.stdout.write(f'Reading Principles from {file_path}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        created_count = 0
        updated_count = 0

        # --- 1. Governance Protocols ---
        protocol_header = soup.find('h2', string='🧠 بروتوكول الحفاظ على الذاكرة')
        if protocol_header:
            protocol_list = protocol_header.find_next_sibling('ol')
            if protocol_list:
                for li in protocol_list.find_all('li'):
                    name = li.find('strong').text.strip() if li.find('strong') else li.text.split(':')[0].strip()
                    description = li.text.strip()
                    obj, created = GuidingPrinciple.objects.update_or_create(
                        name=name,
                        defaults={'principle_type': 'حوكمة', 'description': description}
                    )
                    self.log_creation(obj, created)
                    if created: created_count += 1
                    else: updated_count += 1

        # --- 2. Engineering Principles ---
        engineering_header = soup.find('h2', string='🧭 المبادئ الهندسية العليا (Non-Negotiables)')
        if engineering_header:
            engineering_list = engineering_header.find_next_sibling('ol')
            if engineering_list:
                for li in engineering_list.find_all('li'):
                    name = li.find('strong').text.strip() if li.find('strong') else li.text.split(':')[0].strip()
                    description = li.text.strip()
                    obj, created = GuidingPrinciple.objects.update_or_create(
                        name=name,
                        defaults={'principle_type': 'هندسي', 'description': description}
                    )
                    self.log_creation(obj, created)
                    if created: created_count += 1
                    else: updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nImport complete. {created_count} created, {updated_count} updated.'))

    def log_creation(self, obj, created):
        if created:
            self.stdout.write(self.style.SUCCESS(f'CREATED: {obj.name}'))
        else:
            self.stdout.write(f'UPDATED: {obj.name}')