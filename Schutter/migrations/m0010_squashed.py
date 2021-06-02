# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
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
        ('Account', 'm0019_squashed'),
        ('BasisTypen', 'm0020_squashed'),
        ('NhbStructuur', 'm0019_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='SchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heeft_interesse', models.BooleanField(default=True)),
                ('voor_wedstrijd', models.BooleanField(default=False)),
                ('boogtype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BasisTypen.boogtype')),
                ('nhblid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.nhblid')),
            ],
            options={
                'verbose_name': 'SchutterBoog',
                'verbose_name_plural': 'SchuttersBoog',
            },
        ),
        migrations.CreateModel(
            name='SchutterVoorkeuren',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voorkeur_dutchtarget_18m', models.BooleanField(default=False)),
                ('voorkeur_meedoen_competitie', models.BooleanField(default=True)),
                ('nhblid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NhbStructuur.nhblid')),
                ('opmerking_para_sporter', models.CharField(default='', max_length=256)),
                ('voorkeur_discipline_25m1pijl', models.BooleanField(default=True)),
                ('voorkeur_discipline_3d', models.BooleanField(default=True)),
                ('voorkeur_discipline_clout', models.BooleanField(default=True)),
                ('voorkeur_discipline_indoor', models.BooleanField(default=True)),
                ('voorkeur_discipline_outdoor', models.BooleanField(default=True)),
                ('voorkeur_discipline_run', models.BooleanField(default=True)),
                ('voorkeur_discipline_veld', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Schutter voorkeuren',
                'verbose_name_plural': 'Schutter voorkeuren',
            },
        ),
    ]

# end of file
