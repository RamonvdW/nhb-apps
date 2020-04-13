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
        ('BasisTypen', 'm0007_volgorde'),
        ('Competitie', 'm0006_delete-competitiewedstrijdklasse'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='teamtypeboog',
            name='boogtype',
        ),
        migrations.RemoveField(
            model_name='teamtypeboog',
            name='teamtype',
        ),
        migrations.RemoveField(
            model_name='wedstrijdklasseboog',
            name='boogtype',
        ),
        migrations.RemoveField(
            model_name='wedstrijdklasseboog',
            name='wedstrijdklasse',
        ),
        migrations.RemoveField(
            model_name='wedstrijdklasseleeftijd',
            name='leeftijdsklasse',
        ),
        migrations.RemoveField(
            model_name='wedstrijdklasseleeftijd',
            name='wedstrijdklasse',
        ),
        migrations.DeleteModel(
            name='TeamType',
        ),
        migrations.DeleteModel(
            name='TeamTypeBoog',
        ),
        migrations.DeleteModel(
            name='WedstrijdKlasse',
        ),
        migrations.DeleteModel(
            name='WedstrijdKlasseBoog',
        ),
        migrations.DeleteModel(
            name='WedstrijdKlasseLeeftijd',
        ),
        migrations.CreateModel(
            name='IndivWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('niet_voor_rk_bk', models.BooleanField()),
                ('is_onbekend', models.BooleanField(default=False)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.BoogType')),
                ('leeftijdsklassen', models.ManyToManyField(to='BasisTypen.LeeftijdsKlasse')),
            ],
            options={
                'verbose_name': 'Wedstrijdklasse',
                'verbose_name_plural': 'Wedstrijdklassen',
            },
        ),
        migrations.CreateModel(
            name='TeamWedstrijdklasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buiten_gebruik', models.BooleanField(default=False)),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('boogtypen', models.ManyToManyField(to='BasisTypen.BoogType')),
            ],
            options={
                'verbose_name': 'Team Wedstrijdklasse',
                'verbose_name_plural': 'Team Wedstrijdklassen',
            },
        ),
    ]

# end of file
