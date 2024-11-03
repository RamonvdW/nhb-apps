# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    replaces = [('HistComp', 'm0015_squashed'),
                ('HistComp', 'm0016_counts')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='HistCompSeizoen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seizoen', models.CharField(max_length=9)),
                ('comp_type', models.CharField(choices=[('18', 'Indoor'), ('25', '25m1pijl')], max_length=2)),
                ('aantal_beste_scores', models.PositiveSmallIntegerField(default=6)),
                ('is_openbaar', models.BooleanField(default=True)),
                ('heeft_uitslag_rk_indiv', models.BooleanField(default=False)),
                ('heeft_uitslag_bk_indiv', models.BooleanField(default=False)),
                ('heeft_uitslag_regio_teams', models.BooleanField(default=False)),
                ('heeft_uitslag_rk_teams', models.BooleanField(default=False)),
                ('heeft_uitslag_bk_teams', models.BooleanField(default=False)),
                ('indiv_bogen', models.CharField(max_length=20)),
                ('team_typen', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': 'Hist seizoen',
                'verbose_name_plural': 'Hist seizoenen',
                'ordering': ['-seizoen', 'comp_type'],
            },
        ),
        migrations.CreateModel(
            name='HistCompRegioTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seizoen', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompseizoen')),
                ('team_klasse', models.CharField(max_length=30)),
                ('team_type', models.CharField(max_length=5)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(max_length=35)),
                ('regio_nr', models.PositiveSmallIntegerField()),
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
            ],
            options={
                'verbose_name': 'Hist regio teams',
                'verbose_name_plural': 'Hist regio teams',
                'ordering': ['rank', 'team_klasse'],
            },
        ),
        migrations.CreateModel(
            name='HistKampIndivRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seizoen', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompseizoen')),
                ('indiv_klasse', models.CharField(max_length=35)),
                ('sporter_lid_nr', models.PositiveIntegerField()),
                ('sporter_naam', models.CharField(max_length=50)),
                ('boogtype', models.CharField(max_length=5)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('vereniging_plaats', models.CharField(default='', max_length=35)),
                ('rayon_nr', models.PositiveSmallIntegerField()),
                ('rank_rk', models.PositiveSmallIntegerField()),
                ('rk_score_is_blanco', models.BooleanField(default=False)),
                ('rk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('rk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('rk_score_totaal', models.PositiveSmallIntegerField(default=0)),
                ('rk_counts', models.CharField(blank=True, default='', max_length=20)),
                ('teams_rk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('teams_rk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('teams_bk_score_1', models.PositiveSmallIntegerField(default=0)),
                ('teams_bk_score_2', models.PositiveSmallIntegerField(default=0)),
                ('titel_code_rk', models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')],
                                                   default=' ', max_length=1)),
            ],
            options={
                'verbose_name': 'Hist indiv RK',
                'verbose_name_plural': 'Hist indiv RK',
            },
        ),
        migrations.CreateModel(
            name='HistCompRegioIndiv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveSmallIntegerField()),
                ('sporter_lid_nr', models.PositiveIntegerField()),
                ('sporter_naam', models.CharField(max_length=50)),
                ('vereniging_nr', models.PositiveSmallIntegerField()),
                ('vereniging_naam', models.CharField(max_length=50)),
                ('boogtype', models.CharField(max_length=5)),
                ('score1', models.PositiveSmallIntegerField(default=0)),
                ('score2', models.PositiveSmallIntegerField(default=0)),
                ('score3', models.PositiveSmallIntegerField(default=0)),
                ('score4', models.PositiveSmallIntegerField(default=0)),
                ('score5', models.PositiveSmallIntegerField(default=0)),
                ('score6', models.PositiveSmallIntegerField(default=0)),
                ('score7', models.PositiveSmallIntegerField(default=0)),
                ('totaal', models.PositiveSmallIntegerField()),
                ('gemiddelde', models.DecimalField(decimal_places=3, max_digits=5)),
                ('laagste_score_nr', models.PositiveSmallIntegerField(default=0)),
                ('seizoen', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompseizoen')),
                ('indiv_klasse', models.CharField(max_length=35)),
                ('vereniging_plaats', models.CharField(max_length=35)),
                ('regio_nr', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Hist indiv regio',
                'verbose_name_plural': 'Hist indiv regio',
                'ordering': ['rank'],
            },
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
                ('titel_code_bk', models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')],
                                                   default=' ', max_length=1)),
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
        migrations.CreateModel(
            name='HistKampTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seizoen', models.ForeignKey(on_delete=models.deletion.CASCADE, to='HistComp.histcompseizoen')),
                ('rk_of_bk', models.CharField(choices=[('R', 'RK'), ('B', 'BK')], default='R', max_length=1)),
                ('rayon_nr', models.PositiveSmallIntegerField(default=0)),
                ('teams_klasse', models.CharField(max_length=30)),
                ('team_type', models.CharField(max_length=5)),
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
                ('lid_1', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                            related_name='team_lid_1', to='HistComp.histkampindivrk')),
                ('lid_2', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                            related_name='team_lid_2', to='HistComp.histkampindivrk')),
                ('lid_3', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                            related_name='team_lid_3', to='HistComp.histkampindivrk')),
                ('lid_4', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                            related_name='team_lid_4', to='HistComp.histkampindivrk')),
                ('titel_code', models.CharField(choices=[(' ', 'None'), ('R', 'RK'), ('B', 'BK'), ('N', 'NK')],
                                                default=' ', max_length=1)),
                ('team_score_counts', models.CharField(blank=True, default='', max_length=20)),
            ],
            options={
                'verbose_name': 'Hist RK/BK teams',
                'verbose_name_plural': 'Hist RK/BK teams',
            },
        ),
    ]

# end of file
