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
        ('BasisTypen', 'm0009_basistypen_2020'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Wedstrijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('preliminair', models.BooleanField(default=True)),
                ('datum', models.DateField()),
                ('tijd_begin_aanmelden', models.TimeField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('tijd_einde_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(to='BasisTypen.IndivWedstrijdklasse')),
            ],
            options={'verbose_name': 'Wedstrijd', 'verbose_name_plural': 'Wedstrijden'},
        ),
        migrations.CreateModel(
            name='WedstrijdLocatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zichtbaar', models.BooleanField(default=True)),
                ('baan_type', models.CharField(choices=[('X', 'Onbekend'), ('O', 'Volledig overdekte binnenbaan'), ('H', 'Binnen-buiten schieten')], default='X', max_length=1)),
                ('verenigingen', models.ManyToManyField(to='NhbStructuur.NhbVereniging')),
                ('banen_18m', models.PositiveSmallIntegerField(default=0)),
                ('banen_25m', models.PositiveSmallIntegerField(default=0)),
                ('max_dt_per_baan', models.PositiveSmallIntegerField(default=4)),
                ('adres', models.TextField(blank=True, max_length=256)),
                ('adres_uit_crm', models.BooleanField(default=False)),
                ('notities', models.TextField(blank=True, max_length=1024)),
            ],
            options={'verbose_name': 'Wedstrijdlocatie', 'verbose_name_plural': 'Wedstrijdlocaties'},
        ),
        migrations.CreateModel(
            name='WedstrijdenPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hiaat', models.BooleanField(default=True)),
                ('wedstrijden', models.ManyToManyField(to='Wedstrijden.Wedstrijd')),
            ],
            options={'verbose_name': 'Wedstrijdenplan', 'verbose_name_plural': 'Wedstrijdenplannen'},
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='locatie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.WedstrijdLocatie'),
        ),
        migrations.AddField(
            model_name='wedstrijd',
            name='team_klassen',
            field=models.ManyToManyField(to='BasisTypen.TeamWedstrijdklasse'),
        ),
    ]

# end of file
