import pandas as pd
from django.core.management.base import BaseCommand
from coredata.models import Student
from datetime import datetime, timedelta
import os
import re

class Command(BaseCommand):
    help = 'Import students from an Excel file with multiple sheets (Grades 7-12)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The absolute path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}'))

        try:
            # Load the Excel file
            xls = pd.ExcelFile(file_path)
            
            total_created = 0
            total_updated = 0
            total_skipped = 0

            # Regex to extract grade number from sheet name (e.g., "الصف- 07" -> "7")
            grade_pattern = re.compile(r'(\d+)')

            for sheet_name in xls.sheet_names:
                clean_sheet_name = str(sheet_name).strip()
                
                # Try to find a number in the sheet name
                match = grade_pattern.search(clean_sheet_name)
                if not match:
                    self.stdout.write(self.style.WARNING(f'Skipping sheet "{sheet_name}" (No number found)'))
                    continue
                
                grade_number = str(int(match.group(1))) # Convert to int then str to remove leading zeros (07 -> 7)
                
                # Check if it's a target grade (7-12)
                if grade_number not in ['7', '8', '9', '10', '11', '12']:
                    self.stdout.write(self.style.WARNING(f'Skipping sheet "{sheet_name}" (Grade {grade_number} not in target 7-12)'))
                    continue

                self.stdout.write(f'Processing Sheet: "{clean_sheet_name}" -> Grade: {grade_number}...')
                
                # Read the sheet
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Normalize column names (strip spaces, lowercase)
                df.columns = df.columns.str.strip().str.lower()
                
                for index, row in df.iterrows():
                    try:
                        # 1. Extract and Clean Data
                        national_no = self.clean_qid(row.get('national_no'))
                        if not national_no:
                            # self.stdout.write(self.style.WARNING(f'  Row {index+2}: Skipped (Missing National No)'))
                            total_skipped += 1
                            continue

                        student_data = {
                            'name_ar': str(row.get('studant_name', '')).strip(),
                            'name_en': str(row.get('studant_englisf_name', '')).strip(),
                            'date_of_birth': self.parse_excel_date(row.get('date_of_birth')),
                            'needs': str(row.get('needs', 'لا')).strip(),
                            'grade': grade_number, # Use the extracted grade number
                            'section': self.clean_number(row.get('section')),
                            
                            'parent_national_no': self.clean_qid(row.get('parent_national_no')),
                            'parent_name': str(row.get('name_parent', '')).strip(),
                            'parent_relation': str(row.get('relation_parent', '')).strip(),
                            'parent_phone': self.clean_phone(row.get('parent_phone_no')),
                            'parent_email': self.clean_email(row.get('parent_email')),
                        }

                        # 2. Update or Create
                        student, created = Student.objects.update_or_create(
                            national_no=national_no,
                            defaults=student_data
                        )

                        if created:
                            total_created += 1
                        else:
                            total_updated += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error in row {index+2}: {str(e)}'))
                        total_skipped += 1

            self.stdout.write(self.style.SUCCESS('---------------------------------------------------'))
            self.stdout.write(self.style.SUCCESS(f'IMPORT COMPLETE'))
            self.stdout.write(self.style.SUCCESS(f'Created: {total_created}'))
            self.stdout.write(self.style.SUCCESS(f'Updated: {total_updated}'))
            self.stdout.write(self.style.ERROR(f'Skipped/Failed (mostly empty rows): {total_skipped}'))
            self.stdout.write(self.style.SUCCESS('---------------------------------------------------'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Critical Error: {str(e)}'))

    def clean_qid(self, value):
        """Converts Arabic/English numbers to string, removes decimals."""
        if pd.isna(value): return None
        s = str(value).strip().replace('.0', '')
        if not s or s.lower() == 'nan': return None
        return self.to_english_numbers(s)

    def clean_number(self, value):
        """Cleans simple numbers like section."""
        if pd.isna(value): return ''
        s = str(value).strip().replace('.0', '')
        return self.to_english_numbers(s)

    def clean_phone(self, value):
        """Takes the first phone number if multiple exist."""
        if pd.isna(value): return None
        s = str(value).strip()
        if not s or s == '-': return None
        # Handle "50877402, 55509522" -> take first one
        if ',' in s:
            s = s.split(',')[0].strip()
        return self.to_english_numbers(s)

    def clean_email(self, value):
        if pd.isna(value) or str(value).strip() == '-': return None
        return str(value).strip()

    def to_english_numbers(self, s):
        """Converts Arabic numerals to English."""
        if not s: return s
        arabic_nums = '٠١٢٣٤٥٦٧٨٩'
        english_nums = '0123456789'
        translation_table = str.maketrans(arabic_nums, english_nums)
        return s.translate(translation_table)

    def parse_excel_date(self, value):
        """
        Handles Excel serial dates (e.g., 41255) and standard strings.
        Excel base date is usually Dec 30, 1899.
        """
        if pd.isna(value): return None
        
        # If it's already a datetime object (pandas sometimes does this automatically)
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.date()

        # If it's a number (Excel Serial)
        try:
            serial = float(value)
            # Excel base date: 1899-12-30
            base_date = datetime(1899, 12, 30)
            delta = timedelta(days=serial)
            return (base_date + delta).date()
        except (ValueError, TypeError):
            pass

        # If it's a string, try parsing common formats
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except ValueError:
            pass
            
        return None