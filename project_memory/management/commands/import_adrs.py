import os
import re
from bs4 import BeautifulSoup
from datetime import date
from django.core.management.base import BaseCommand
from django.conf import settings
from project_memory.models import ArchitecturalDecision

class Command(BaseCommand):
    help = 'Imports ALL Architectural Decision Records (ADRs) from the HTML memory file, robustly.'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'memory', '06_Architecture_Decision_Log.html')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(f'Reading ALL ADRs from {file_path}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Find all h3 tags that look like an ADR title
        adr_headers = soup.find_all('h3', string=re.compile(r'\s*ADR-\d+'))
        
        if not adr_headers:
            self.stdout.write(self.style.WARNING('No ADR headers found.'))
            return

        created_count = 0
        updated_count = 0

        for header in adr_headers:
            try:
                title_text = header.text.strip()
                adr_id_match = re.search(r'(ADR-\d+)', title_text)
                if not adr_id_match:
                    self.stdout.write(self.style.WARNING(f"Skipping header without ADR-ID: {title_text}"))
                    continue
                
                adr_id = adr_id_match.group(1)
                title = title_text.replace(f'{adr_id}:', '').strip()

                # Find the associated list of details robustly
                ul = header.find_next('ul')
                if not ul:
                    self.stdout.write(self.style.WARNING(f'Could not find details list for {adr_id}'))
                    continue

                details = {}
                for li in ul.find_all('li'):
                    strong_tag = li.find('strong')
                    if strong_tag:
                        key = strong_tag.text.strip().replace(':', '')
                        # Robustly get the value after the <strong> tag
                        value = (strong_tag.next_sibling or '').strip()
                        if not value and li.find('ol'): # Handle nested lists like in ADR-008
                            value = ' '.join(item.text for item in li.find('ol').find_all('li'))
                        details[key] = value

                # --- Data Validation and Cleaning ---
                date_str = details.get('التاريخ', '').strip()
                if not date_str:
                    # Try to get it from a <time> tag if it exists
                    time_tag = ul.find('time')
                    if time_tag and time_tag.has_attr('datetime'):
                        date_str = time_tag['datetime']
                    else:
                        self.stdout.write(self.style.WARNING(f"Date not found for {adr_id}. Using today's date."))
                        date_str = date.today().isoformat()

                status = details.get('الحالة', 'منفذ').strip() or 'منفذ'
                context = details.get('السياق', '').strip()
                decision = details.get('القرار', '').strip()
                justification = details.get('المبررات', '').strip()

                # Create or update the ADR in the database
                adr_obj, created = ArchitecturalDecision.objects.update_or_create(
                    adr_id=adr_id,
                    defaults={
                        'title': title,
                        'date': date_str,
                        'status': status,
                        'context': context,
                        'decision': decision,
                        'justification': justification,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'CREATED: {adr_obj}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'UPDATED: {adr_obj}')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process an ADR near '{header.text.strip()}': {e}"))


        self.stdout.write(self.style.SUCCESS(f'\nImport complete. {created_count} created, {updated_count} updated.'))