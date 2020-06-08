# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0009_basistypen_2020'),
        ('Wedstrijden', 'm0001_locatie'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Wedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('preliminair', models.BooleanField(default=True)),
                ('datum_wanneer', models.DateField()),
                ('tijd_begin_aanmelden', models.TimeField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('tijd_einde_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(to='BasisTypen.IndivWedstrijdklasse')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdLocatie')),
                ('team_klassen', models.ManyToManyField(to='BasisTypen.TeamWedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Wedstrijd',
                'verbose_name_plural': 'Wedstrijden',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdenPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bevat_hiaat', models.BooleanField(default=True)),
                ('wedstrijden', models.ManyToManyField(to='Wedstrijden.Wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijdenplan',
                'verbose_name_plural': 'Wedstrijdenplannen',
            },
        ),
    ]

# end of file
