from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('coredata', '0022_fix_remaining_table_names'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='evidencefile',
            table='coredata_evidencefile',
        ),
    ]