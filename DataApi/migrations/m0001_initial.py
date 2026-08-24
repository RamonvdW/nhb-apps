# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # afhankelijkheden
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='DataApiLidmaatschap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aanmeld_datum', models.CharField(max_length=10)),
                ('afmeld_datum', models.CharField(max_length=10, default='')),
                ('geboorte_datum', models.CharField(max_length=10)),
                ('geslacht', models.CharField(max_length=1)),
                ('land_iso', models.CharField(max_length=2)),
                ('postcode', models.CharField(max_length=20)),
                ('lid_nr', models.PositiveIntegerField()),
                ('ver_nr', models.PositiveIntegerField()),
            ],
            options={'verbose_name': 'DataApi Lidmaatschap',
                     'verbose_name_plural': 'DataApi Lidmaatschappen'},
        ),
        migrations.CreateModel(
            name='DataApiVereniging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ver_nr', models.PositiveIntegerField()),
                ('naam', models.CharField(max_length=50)),
                ('aanmeld_datum', models.CharField(max_length=10)),
                ('afmeld_datum', models.CharField(max_length=10, default='')),
                ('kvk_nummer', models.CharField(blank=True, default='', max_length=15)),
                ('straatnaam', models.CharField(max_length=100)),
                ('huisnummer', models.PositiveIntegerField()),
                ('postcode', models.CharField(max_length=6)),
                ('plaats', models.CharField(max_length=50)),
                ('land_iso', models.CharField(default='NL', max_length=2)),
                ('lat', models.CharField(max_length=10)),
                ('lon', models.CharField(max_length=10)),
            ],
            options={'verbose_name': 'DataApi Vereniging',
                     'verbose_name_plural': 'DataApi Verenigingen'},
        ),
    ]

# end of file
