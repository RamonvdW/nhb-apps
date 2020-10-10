# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
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
        ('BasisTypen', 'm0010_squashed'),
        ('NhbStructuur', 'm0015_squashed'),
        ('Score', 'm0005_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdLocatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten')], default='X', max_length=1)),
                ('verenigingen', models.ManyToManyField(blank=True, to='NhbStructuur.NhbVereniging')),
                ('banen_18m', models.PositiveSmallIntegerField(default=0)),
                ('banen_25m', models.PositiveSmallIntegerField(default=0)),
                ('max_dt_per_baan', models.PositiveSmallIntegerField(default=4)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('adres_uit_crm', models.BooleanField(default=False)),
                ('notities', models.TextField(blank=True, max_length=1024)),
            ],
            options={
                'verbose_name': 'Wedstrijdlocatie',
                'verbose_name_plural': 'Wedstrijdlocaties',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdUitslag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.PositiveSmallIntegerField()),
                ('afstand_meter', models.PositiveSmallIntegerField()),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
                ('is_bevroren', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Wedstrijduitslag',
                'verbose_name_plural': 'Wedstrijduitslagen',
            },
        ),
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
                ('indiv_klassen', models.ManyToManyField(blank=True, to='BasisTypen.IndivWedstrijdklasse')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbVereniging')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdLocatie')),
                ('team_klassen', models.ManyToManyField(blank=True, to='BasisTypen.TeamWedstrijdklasse')),
                ('uitslag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdUitslag')),
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
                ('wedstrijden', models.ManyToManyField(blank=True, to='Wedstrijden.Wedstrijd')),
            ],
            options={
                'verbose_name': 'Wedstrijdenplan',
                'verbose_name_plural': 'Wedstrijdenplannen',
            },
        ),
    ]

# end of file
