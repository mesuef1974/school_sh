import os
import shutil
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess

class Command(BaseCommand):
    help = 'Generates a full backup of the Database and Media files.'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            self.stdout.write(self.style.SUCCESS(f"Created backup directory: {backup_dir}"))

        backup_filename = f"platform_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Temporary directory for DB dump
        temp_dir = os.path.join(backup_dir, f"temp_{timestamp}")
        os.makedirs(temp_dir)
        db_dump_path = os.path.join(temp_dir, 'database.sql')

        db_config = settings.DATABASES['default']
        
        self.stdout.write("Starting Database Export...")
        
        try:
            # Set environment variable for password to avoid interactive prompt
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            # Using pg_dump
            cmd = [
                'pg_dump',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '-f', db_dump_path,
                db_config['NAME']
            ]
            
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            self.stdout.write(self.style.SUCCESS("Database Export Successful."))
            
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"Database Export Failed: {e.stderr.decode()}"))
            # If pg_dump fails, we still try to backup media if requested, or just fail
            shutil.rmtree(temp_dir)
            return
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR("pg_dump not found in system path. Please ensure PostgreSQL tools are installed."))
            shutil.rmtree(temp_dir)
            return

        self.stdout.write("Compressing Backup (DB + Media)...")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add DB dump
                zipf.write(db_dump_path, arcname='database.sql')
                
                # Add Media files
                media_root = settings.MEDIA_ROOT
                if os.path.exists(media_root):
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join('media', os.path.relpath(file_path, media_root))
                            zipf.write(file_path, arcname=arcname)
                
            self.stdout.write(self.style.SUCCESS(f"Backup created successfully: {backup_path}"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Compression failed: {str(e)}"))
        
        finally:
            shutil.rmtree(temp_dir)

        # Cleanup old backups (keep last 5)
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('platform_backup_')], reverse=True)
        if len(backups) > 5:
            for old_backup in backups[5:]:
                os.remove(os.path.join(backup_dir, old_backup))
                self.stdout.write(f"Removed old backup: {old_backup}")
