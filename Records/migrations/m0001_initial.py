# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """ Migratie classs voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0002_nhbstructuur_2018'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='IndivRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveIntegerField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
                ('soort_record', models.CharField(max_length=40)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('leeftijdscategorie', models.CharField(choices=[('M', 'Master'), ('S', 'Senior'), ('J', 'Junior'), ('C', 'Cadet'), ('U', 'Uniform (para)')], max_length=1)),
                ('materiaalklasse', models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'), ('LB', 'Longbow'), ('IB', 'Instinctive bow'), ('O', 'Overige')], max_length=2)),
                ('materiaalklasse_overig', models.CharField(max_length=20, blank=True)),
                ('naam', models.CharField(max_length=50)),
                ('datum', models.DateField()),
                ('plaats', models.CharField(max_length=50)),
                ('land', models.CharField(max_length=50)),
                ('score', models.PositiveIntegerField()),
                ('score_notitie', models.CharField(max_length=10, blank=True)),
                ('is_national_record', models.BooleanField(default=False)),
                ('is_european_record', models.BooleanField(default=False)),
                ('is_world_record', models.BooleanField(default=False)),
                ('nhb_lid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.NhbLid')),
            ],
            options={
                'verbose_name': 'Individueel record',
                'verbose_name_plural': 'Individuele records',
            },
        ),
    ]

# end of file

