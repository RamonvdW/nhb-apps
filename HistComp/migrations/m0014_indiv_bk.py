# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0013_titels'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='histcompregioindiv',
            options={'ordering': ['rank'], 'verbose_name': 'Hist indiv regio', 'verbose_name_plural': 'Hist indiv regio'},
        ),
        migrations.AlterModelOptions(
            name='histkampindiv',
            options={'verbose_name': 'Hist indiv RK', 'verbose_name_plural': 'Hist indiv RK'},
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='bk_counts',
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='bk_score_1',
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='bk_score_2',
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='bk_score_totaal',
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='rank_bk',
        ),
        migrations.RemoveField(
            model_name='histkampindiv',
            name='titel_code_bk',
        ),
        migrations.CreateModel(
            name='HistKampIndivBK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bk_indiv_klasse', models.CharField(max_length=35)),
                ('sporter_lid_nr', models.PositiveIntegerField()),
                ('sporter_naam', models.CharField(max_length=50)),
                ('boogtype', models.CharField(max_length=5)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(default='', max_length=35)),
                ('rank_bk', models.PositiveSmallIntegerField(default=0)),
                ('titel_code_bk', models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')], default=' ', max_length=1)),
                ('bk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('bk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('bk_score_totaal', models.PositiveSmallIntegerField(default=0)),
                ('bk_counts', models.CharField(blank=True, default='', max_length=20)),
                ('seizoen', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompseizoen')),
            ],
            options={
                'verbose_name': 'Hist indiv BK',
                'verbose_name_plural': 'Hist indiv BK',
            },
        ),
    ]

# end of file
