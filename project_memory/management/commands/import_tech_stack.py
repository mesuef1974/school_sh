import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from project_memory.models import Technology

class Command(BaseCommand):
    help = 'Imports the Tech Stack from the HTML memory file.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'memory', '03_System_Architecture.html')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found at: {file_path}'))
            return

        self.stdout.write(f'Reading Tech Stack from {file_path}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Find the specific table for the tech stack
        tech_stack_header = soup.find('h2', string='🧱 المكدس التقني الكامل (Full Tech Stack)')
        if not tech_stack_header:
            self.stdout.write(self.style.ERROR('Tech Stack table header not found.'))
            return
            
        table = tech_stack_header.find_next_sibling('table')
        if not table:
            self.stdout.write(self.style.ERROR('Tech Stack table not found after header.'))
            return

        created_count = 0
        updated_count = 0

        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 3:
                layer = cells[0].text.strip()
                tech_text = cells[1].text.strip()
                purpose = cells[2].text.strip()

                # Split tech name and version
                name = tech_text
                version = None
                if ' ' in tech_text:
                    parts = tech_text.split(' ', 1)
                    name = parts[0]
                    version = parts[1]

                tech_obj, created = Technology.objects.update_or_create(
                    name=name,
                    defaults={
                        'layer': layer,
                        'version': version,
                        'purpose': purpose,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'CREATED: {tech_obj.name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'UPDATED: {tech_obj.name}')

        self.stdout.write(self.style.SUCCESS(f'\nImport complete. {created_count} created, {updated_count} updated.'))