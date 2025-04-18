# Generated by Django 4.2.20 on 2025-04-03 17:43

from django.db import migrations, models
from ImportCRM.models import IMPORT_LIMIETEN_PK


def init_limieten(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    klas = apps.get_model('ImportCRM', 'ImportLimieten')

    # maak het enige record aan met de specifieke primary key
    klas(pk=IMPORT_LIMIETEN_PK).save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ImportLimieten',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('use_limits', models.BooleanField(default=True)),
                ('max_club_changes', models.PositiveSmallIntegerField(default=50)),
                ('max_member_changes', models.PositiveSmallIntegerField(default=250)),
            ],
            options={
                'verbose_name': 'Import limieten',
                'verbose_name_plural': 'Import limieten',
            },
        ),
        migrations.RunPython(init_limieten),
    ]

# end of file
