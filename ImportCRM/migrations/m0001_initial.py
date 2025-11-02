# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from ImportCRM.models import IMPORT_LIMIETEN_PK


def init_limieten(apps, _):
    """ maak het enige record aan in deze tabel """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    klas = apps.get_model('ImportCRM', 'ImportLimieten')

    # maak het enige record aan met de specifieke primary key
    klas(pk=IMPORT_LIMIETEN_PK).save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
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
