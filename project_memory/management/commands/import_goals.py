import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from project_memory.models import ProjectGoal

class Command(BaseCommand):
    help = 'Imports Project Goals, KPIs, and Roadmap from the HTML memory file.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'memory', '02_Goals_And_KPIs.html')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found at: {file_path}'))
            return

        self.stdout.write(f'Reading Goals from {file_path}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        created_count = 0
        updated_count = 0

        # --- 1. North Star Metric ---
        north_star_header = soup.find('h2', string='⭐ الهدف الاستراتيجي الأعلى (The North Star Metric)')
        if north_star_header:
            north_star_p = north_star_header.find_next_sibling('p')
            if north_star_p and north_star_p.find('strong'):
                goal_name = north_star_p.find('strong').text.strip()
                obj, created = ProjectGoal.objects.update_or_create(
                    name=goal_name,
                    defaults={'goal_type': 'استراتيجي', 'description': 'الهدف الأسمى الذي تخدمه جميع الأهداف الأخرى.'}
                )
                self.log_creation(obj, created)
                if created: created_count += 1
                else: updated_count += 1

        # --- 2. Short-term Goals ---
        short_term_header = soup.find('h2', string='🎯 الأهداف قصيرة المدى (الركائز الثلاث) ومؤشرات قياسها')
        if short_term_header:
            tables = short_term_header.find_next_siblings('table')
            for table in tables:
                for row in table.find('tbody').find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) == 3:
                        name = cells[0].text.strip()
                        kpi = cells[1].text.strip()
                        measurement = cells[2].text.strip()
                        obj, created = ProjectGoal.objects.update_or_create(
                            name=name,
                            defaults={'goal_type': 'قصير المدى', 'description': name, 'kpi': kpi, 'measurement': measurement}
                        )
                        self.log_creation(obj, created)
                        if created: created_count += 1
                        else: updated_count += 1
        
        # --- 3. Roadmap / Future Features ---
        roadmap_header = soup.find('h2', string='📍 خارطة الطريق والميزات المستقبلية')
        if roadmap_header:
            # Find all h3 and ul siblings after the roadmap header
            for sibling in roadmap_header.find_next_siblings():
                if sibling.name == 'h3':
                    priority = sibling.text.strip()
                elif sibling.name == 'ul':
                    for li in sibling.find_all('li'):
                        name = li.find('strong').text.strip() if li.find('strong') else li.text.strip().split(':')[0]
                        description = li.text.strip()
                        obj, created = ProjectGoal.objects.update_or_create(
                            name=name,
                            defaults={'goal_type': 'ميزة مستقبلية', 'description': description, 'kpi': priority}
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