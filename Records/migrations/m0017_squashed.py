# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('Records', 'm0014_squashed'),
                ('Records', 'm0015_volgorde'),
                ('Records', 'm0016_sv_icon')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0033_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='IndivRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveIntegerField()),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('18', 'Indoor'), ('25', '25m 1pijl')],
                                                max_length=2)),
                ('soort_record', models.CharField(max_length=40)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('leeftijdscategorie', models.CharField(choices=[('M', 'Master'), ('S', 'Senior'), ('J', 'Junior'),
                                                                 ('C', 'Cadet'), ('U', 'Uniform (para)')],
                                                        max_length=1)),
                ('materiaalklasse', models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'),
                                                              ('LB', 'Longbow'), ('TR', 'Traditional'),
                                                              ('IB', 'Instinctive bow')],
                                                     max_length=2)),
                ('para_klasse', models.CharField(blank=True, max_length=20)),
                ('naam', models.CharField(max_length=50)),
                ('datum', models.DateField()),
                ('plaats', models.CharField(max_length=50)),
                ('land', models.CharField(blank=True, max_length=50)),
                ('score', models.PositiveIntegerField()),
                ('score_notitie', models.CharField(blank=True, max_length=30)),
                ('is_european_record', models.BooleanField(default=False)),
                ('is_world_record', models.BooleanField(default=False)),
                ('max_score', models.PositiveIntegerField(default=0)),
                ('x_count', models.PositiveIntegerField(default=0)),
                ('verbeterbaar', models.BooleanField(default=True)),
                ('sporter', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT,
                                              to='Sporter.sporter')),
            ],
            options={
                'verbose_name': 'Individueel record',
                'verbose_name_plural': 'Individuele records',
            },
        ),
        migrations.CreateModel(
            name='BesteIndivRecords',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveIntegerField(default=0)),
                ('discipline', models.CharField(choices=[('OD', 'Outdoor'), ('18', 'Indoor'), ('25', '25m 1pijl')],
                                                max_length=2)),
                ('soort_record', models.CharField(max_length=40)),
                ('geslacht', models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], max_length=1)),
                ('leeftijdscategorie', models.CharField(choices=[('M', 'Master'), ('S', 'Senior'), ('J', 'Junior'),
                                                                 ('C', 'Cadet'), ('U', 'Uniform (para)')],
                                                        max_length=1)),
                ('materiaalklasse', models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow'),
                                                              ('LB', 'Longbow'), ('TR', 'Traditional'),
                                                              ('IB', 'Instinctive bow')],
                                                     max_length=2)),
                ('para_klasse', models.CharField(blank=True, max_length=20)),
                ('beste', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                            to='Records.indivrecord')),
            ],
            options={
                'verbose_name': 'Beste individuele records',
                'verbose_name_plural': 'Beste individuele records',
            },
        ),
        migrations.CreateModel(
            name='AnderRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(max_length=30)),
                ('sv_icon', models.CharField(max_length=20)),
                ('tekst', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=100)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('datum', models.DateField(default='2000-01-01')),
            ],
            options={
                'verbose_name': 'Ander record',
                'verbose_name_plural': 'Andere records',
            },
        ),
    ]

# end of file
