# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Locatie', 'm0006_squashed'),
                ('Locatie', 'm0007_rename'),
                ('Locatie', 'm0008_evenement_locatie')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Reistijd',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vanaf_lat', models.CharField(default='', max_length=10)),
                ('vanaf_lon', models.CharField(default='', max_length=10)),
                ('naar_lat', models.CharField(default='', max_length=10)),
                ('naar_lon', models.CharField(default='', max_length=10)),
                ('reistijd_min', models.PositiveSmallIntegerField(default=0)),
                ('op_datum', models.DateField(default='2000-01-01')),
            ],
            options={
                'verbose_name': 'Reistijd',
                'verbose_name_plural': 'Reistijden',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdLocatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'),
                                                        ('H', 'Binnen-buiten schieten'), ('B', 'Buitenbaan'),
                                                        ('E', 'Extern')],
                                               default='X', max_length=1)),
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
                ('adres_lat', models.CharField(blank=True, default='', max_length=10)),
                ('adres_lon', models.CharField(blank=True, default='', max_length=10)),
            ],
            options={
                'verbose_name': 'Wedstrijd locatie',
            },
        ),
        migrations.CreateModel(
            name='EvenementLocatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('zichtbaar', models.BooleanField(default=True)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('plaats', models.CharField(blank=True, default='', max_length=50)),
                ('notities', models.TextField(blank=True, max_length=1024)),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Evenement locatie',
            },
        ),
    ]

# end of file
