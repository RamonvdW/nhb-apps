# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    initial = True

    # volgorde afdwingen
    dependencies = [
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='BoogType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=50)),
                ('afkorting', models.CharField(max_length=5)),
            ],
            options={
                'verbose_name': 'Boog type',
                'verbose_name_plural': 'Boog types',
            },
        ),
        migrations.CreateModel(
            name='LeeftijdsKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('afkorting', models.CharField(max_length=5)),
                ('beschrijving', models.CharField(max_length=80)),
                ('klasse_kort', models.CharField(max_length=30)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('max_wedstrijdleeftijd', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Leeftijdsklasse',
                'verbose_name_plural': 'Leeftijdsklassen',
            },
        ),
        migrations.CreateModel(
            name='TeamType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=80)),
            ],
            options={
                'verbose_name': 'Team type',
                'verbose_name_plural': 'Team types',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=80)),
                ('niet_voor_rk_bk', models.BooleanField()),
                ('is_voor_teams', models.BooleanField()),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
            ],
            options={
                'verbose_name': 'Wedstrijdklasse',
                'verbose_name_plural': 'Wedstrijdklassen',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdKlasseLeeftijd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leeftijdsklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.LeeftijdsKlasse')),
                ('wedstrijdklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.WedstrijdKlasse')),
            ],
            options={
                'verbose_name': 'Leeftijdsklasse voor een wedstrijdklasse',
                'verbose_name_plural': 'Leeftijdsklassen voor elk wedstrijdklasse',
            },
        ),
        migrations.CreateModel(
            name='WedstrijdKlasseBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.BoogType')),
                ('wedstrijdklasse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.WedstrijdKlasse')),
            ],
            options={
                'verbose_name': 'Boog voor een wedstrijdklasse',
                'verbose_name_plural': 'Bogen voor elke wedstrijdklasse',
            },
        ),
        migrations.CreateModel(
            name='TeamTypeBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.BoogType')),
                ('teamtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.TeamType')),
            ],
            options={
                'verbose_name': 'Boog voor een team type',
                'verbose_name_plural': 'Bogen voor een team type',
            },
        ),
    ]

# end of file
