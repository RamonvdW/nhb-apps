# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0016_lid_tot_einde_jaar'),
        ('Competitie', 'm0026_remove_obsolete_fields'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='RegiocompetitieTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
            ],
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='regio_heeft_vaste_teams',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='regio_organiseert_teamcompetitie',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='deelcompetitie',
            name='regio_team_punten_model',
            field=models.CharField(choices=[('2P', 'Twee punten systeem (2/1/0)'), ('3P', 'Drie punten systeem (3/1/0)'), ('SS', 'Cumulatief: som van team totaal elke ronde'), ('F1', 'Formule 1 systeem (10/8/6/5/4/3/2/1)')], default='2P', max_length=2),
        ),
        migrations.CreateModel(
            name='RegiocompetitieTeamPoule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(default='', max_length=100)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('teams', models.ManyToManyField(blank=True, to='Competitie.RegiocompetitieTeam')),
            ],
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='deelcompetitie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie'),
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='klasse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse'),
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='vaste_schutters',
            field=models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog'),
        ),
        migrations.AddField(
            model_name='regiocompetitieteam',
            name='vereniging',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging'),
        ),
        migrations.CreateModel(
            name='RegiocompetitieRondeTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ronde_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_score', models.PositiveSmallIntegerField(default=0)),
                ('team_punten', models.PositiveSmallIntegerField(default=0)),
                ('schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.regiocompetitieteam')),
            ],
        ),
        migrations.CreateModel(
            name='KampioenschapTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
                ('schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
            ],
        ),
    ]

# end of file
