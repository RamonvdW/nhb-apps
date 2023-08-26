# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

"""
    Migratie plan:
    
    1. Maak nieuwe Locatie
    2. Kopieer locaties + zet referentie oud naar nieuw: WedstrijdLocatie.locatie_new = Locatie
    3. Migratie andere modellen:
            voeg locatie_new toe
            verwijder veld locatie
            hernoem veld locatie_new naar locatie
"""


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0003_vereniging_2'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Locatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten'), ('B', 'Buitenbaan'), ('E', 'Extern')], default='X', max_length=1)),
                ('discipline_25m1pijl', models.BooleanField(default=False)),
                ('discipline_outdoor', models.BooleanField(default=False)),
                ('discipline_indoor', models.BooleanField(default=False)),
                ('discipline_clout', models.BooleanField(default=False)),
                ('discipline_veld', models.BooleanField(default=False)),
                ('discipline_run', models.BooleanField(default=False)),
                ('discipline_3d', models.BooleanField(default=False)),
                ('banen_18m', models.PositiveSmallIntegerField(default=0)),
                ('banen_25m', models.PositiveSmallIntegerField(default=0)),
                ('max_sporters_18m', models.PositiveSmallIntegerField(default=0)),
                ('max_sporters_25m', models.PositiveSmallIntegerField(default=0)),
                ('buiten_banen', models.PositiveSmallIntegerField(default=0)),
                ('buiten_max_afstand', models.PositiveSmallIntegerField(default=0)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('plaats', models.CharField(blank=True, default='', max_length=50)),
                ('adres_uit_crm', models.BooleanField(default=False)),
                ('notities', models.TextField(blank=True, max_length=1024)),
                ('verenigingen', models.ManyToManyField(to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Locatie',
            },
        ),
    ]

# end of file
