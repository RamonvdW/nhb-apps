# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0009_renames'),
    ]

    # migratie functies
    operations = [
        migrations.AlterModelOptions(
            name='histcompetitie',
            options={'ordering': ['seizoen', 'comp_type'], 'verbose_name': 'Historie competitie', 'verbose_name_plural': 'Historie competitie'},
        ),
        migrations.AlterModelOptions(
            name='histcompregioindiv',
            options={'ordering': ['rank'], 'verbose_name': 'Hist regio indiv', 'verbose_name_plural': 'Hist regio indiv'},
        ),
        migrations.AddField(
            model_name='histcompregioindiv',
            name='klasse_indiv',
            field=models.CharField(default='', max_length=35),
        ),
        migrations.AddField(
            model_name='histcompregioindiv',
            name='vereniging_plaats',
            field=models.CharField(default='', max_length=35),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='boogtype',
            field=models.CharField(default='', max_length=5),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='laagste_score_nr',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='rank',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score1',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score2',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score3',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score4',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score5',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score6',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='score7',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='totaal',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='histcompregioindiv',
            name='vereniging_nr',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.CreateModel(
            name='HistCompRegioTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team_klasse', models.CharField(max_length=30)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(max_length=35)),
                ('team_nr', models.PositiveSmallIntegerField()),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('ronde_1_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_2_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_3_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_4_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_5_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_6_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_7_score', models.PositiveSmallIntegerField(default=0)),
                ('ronde_1_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_2_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_3_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_4_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_5_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_6_punten', models.PositiveSmallIntegerField(default=0)),
                ('ronde_7_punten', models.PositiveSmallIntegerField(default=0)),
                ('totaal_score', models.PositiveSmallIntegerField(default=0)),
                ('totaal_punten', models.PositiveSmallIntegerField(default=0)),
                ('histcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompetitie')),
            ],
            options={
                'verbose_name': 'Hist regio teams',
                'verbose_name_plural': 'Hist regio teams',
                'ordering': ['rank', 'team_klasse'],
            },
        ),
        migrations.CreateModel(
            name='HistKampIndiv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('histcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompetitie')),
                ('klasse_indiv', models.CharField(max_length=35)),
                ('sporter_lid_nr', models.PositiveIntegerField()),
                ('sporter_naam', models.CharField(max_length=50)),
                ('boogtype', models.CharField(max_length=5)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(default='', max_length=35)),
                ('rank_rk', models.PositiveSmallIntegerField()),
                ('rank_bk', models.PositiveSmallIntegerField(default=0)),
                ('rk_score_is_blanco', models.BooleanField(default=False)),
                ('rk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('rk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('bk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('bk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('teams_rk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('teams_rk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('teams_bk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('teams_bk_score_2', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Hist rk/bk indiv',
                'verbose_name_plural': 'Hist rk/bk indiv',
            },
        ),
        migrations.CreateModel(
            name='HistKampTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rk_of_bk', models.CharField(choices=[('R', 'RK'), ('B', 'BK')], default='R', max_length=1)),
                ('klasse_teams', models.CharField(max_length=30)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(default='', max_length=35)),
                ('team_nr', models.PositiveSmallIntegerField()),
                ('team_score', models.PositiveSmallIntegerField()),
                ('rank', models.PositiveSmallIntegerField()),
                ('score_lid_1', models.PositiveSmallIntegerField(default=0)),
                ('score_lid_2', models.PositiveSmallIntegerField(default=0)),
                ('score_lid_3', models.PositiveSmallIntegerField(default=0)),
                ('score_lid_4', models.PositiveSmallIntegerField(default=0)),
                ('histcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompetitie')),
                ('lid_1', models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, blank=True, related_name='team_lid_1', to='HistComp.histkampindiv')),
                ('lid_2', models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, blank=True, related_name='team_lid_2', to='HistComp.histkampindiv')),
                ('lid_3', models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, blank=True, related_name='team_lid_3', to='HistComp.histkampindiv')),
                ('lid_4', models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, blank=True, related_name='team_lid_4', to='HistComp.histkampindiv')),
            ],
            options={
                'verbose_name': 'Hist rk/bk teams',
                'verbose_name_plural': 'Hist rk/bk teams',
            },
        ),
    ]

# end of file
