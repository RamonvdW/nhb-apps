# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0028_squashed'),
        ('NhbStructuur', 'm0024_squashed'),
        ('Score', 'm0014_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdLocatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten'), ('B', 'Buitenbaan'), ('E', 'Extern')], default='X', max_length=1)),
                ('verenigingen', models.ManyToManyField(blank=True, to='NhbStructuur.NhbVereniging')),
                ('banen_18m', models.PositiveSmallIntegerField(default=0)),
                ('banen_25m', models.PositiveSmallIntegerField(default=0)),
                ('max_dt_per_baan', models.PositiveSmallIntegerField(default=4)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('adres_uit_crm', models.BooleanField(default=False)),
                ('plaats', models.CharField(blank=True, default='', max_length=50)),
                ('notities', models.TextField(blank=True, max_length=1024)),
                ('buiten_banen', models.PositiveSmallIntegerField(default=0)),
                ('buiten_max_afstand', models.PositiveSmallIntegerField(default=0)),
                ('discipline_3d', models.BooleanField(default=False)),
                ('discipline_clout', models.BooleanField(default=False)),
                ('discipline_indoor', models.BooleanField(default=False)),
                ('discipline_outdoor', models.BooleanField(default=False)),
                ('discipline_25m1pijl', models.BooleanField(default=False)),
                ('discipline_run', models.BooleanField(default=False)),
                ('discipline_veld', models.BooleanField(default=False)),
                ('naam', models.CharField(blank=True, max_length=50)),
                ('max_sporters_18m', models.PositiveSmallIntegerField(default=0)),
                ('max_sporters_25m', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Wedstrijd locatie',
                'verbose_name_plural': 'Wedstrijd locaties',
            },
        ),
        migrations.CreateModel(
            name='CompetitieWedstrijdUitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('is_bevroren', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
            ],
            options={
                'verbose_name': 'Competitie Wedstrijd Uitslag',
                'verbose_name_plural': 'Competitie Wedstrijd Uitslagen',
            },
        ),
        migrations.CreateModel(
            name='CompetitieWedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('preliminair', models.BooleanField(default=True)),
                ('datum_wanneer', models.DateField()),
                ('tijd_begin_aanmelden', models.TimeField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('tijd_einde_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(blank=True, to='BasisTypen.IndivWedstrijdklasse')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('team_klassen', models.ManyToManyField(blank=True, to='BasisTypen.TeamWedstrijdklasse')),
                ('uitslag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.competitiewedstrijduitslag')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Competitie Wedstrijd',
                'verbose_name_plural': 'Competitie Wedstrijden',
            },
        ),
        migrations.CreateModel(
            name='CompetitieWedstrijdenPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bevat_hiaat', models.BooleanField(default=True)),
                ('wedstrijden', models.ManyToManyField(blank=True, to='Wedstrijden.CompetitieWedstrijd')),
            ],
            options={
                'verbose_name': 'Competitie Wedstrijden Plan',
                'verbose_name_plural': 'Competitie Wedstrijden Plannen',
            },
        ),
    ]

# end of file
