# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.db.models.deletion


def init_taken(apps, _):
    """ Maak de enige tabel regel aan die gebruikt wordt door het cron job
        regiocomp_upd_tussenstand.
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    taken_klas = apps.get_model('Competitie', 'CompetitieTaken')

    taken_klas().save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0020_squashed'),
        ('Functie', 'm0010_squashed'),
        ('NhbStructuur', 'm0019_squashed'),
        ('Schutter', 'm0010_squashed'),
        ('Score', 'm0009_squashed'),
        ('Wedstrijden', 'm0018_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Competitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=40)),
                ('afstand', models.CharField(choices=[('18', 'Indoor'), ('25', '25m 1pijl')], max_length=2)),
                ('begin_jaar', models.PositiveSmallIntegerField()),
                ('uiterste_datum_lid', models.DateField()),
                ('begin_aanmeldingen', models.DateField()),
                ('einde_aanmeldingen', models.DateField()),
                ('einde_teamvorming', models.DateField()),
                ('eerste_wedstrijd', models.DateField()),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('bk_eerste_wedstrijd', models.DateField()),
                ('bk_laatste_wedstrijd', models.DateField()),
                ('alle_regiocompetities_afgesloten', models.BooleanField(default=False)),
                ('alle_rks_afgesloten', models.BooleanField(default=False)),
                ('alle_bks_afgesloten', models.BooleanField(default=False)),
                ('laatst_mogelijke_wedstrijd', models.DateField()),
                ('rk_eerste_wedstrijd', models.DateField()),
                ('rk_laatste_wedstrijd', models.DateField()),
                ('klassegrenzen_vastgesteld', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitie')),
                ('indiv', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.indivwedstrijdklasse')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.teamwedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Competitie klasse',
                'verbose_name_plural': 'Competitie klassen',
            },
        ),
        migrations.CreateModel(
            name='DeelCompetitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('laag', models.CharField(choices=[('Regio', 'Regiocompetitie'), ('RK', 'Rayoncompetitie'), ('BK', 'Bondscompetitie')], max_length=5)),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitie')),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('functie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Functie.functie')),
                ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.competitiewedstrijdenplan')),
                ('inschrijf_methode', models.CharField(choices=[('1', 'Kies wedstrijden'), ('2', 'Naar locatie wedstrijdklasse'), ('3', 'Voorkeur dagdelen')], default='2', max_length=1)),
                ('toegestane_dagdelen', models.CharField(blank=True, default='', max_length=20)),
                ('heeft_deelnemerslijst', models.BooleanField(default=False)),
                ('regio_heeft_vaste_teams', models.BooleanField(default=True)),
                ('regio_organiseert_teamcompetitie', models.BooleanField(default=True)),
                ('regio_team_punten_model', models.CharField(choices=[('2P', 'Twee punten systeem (2/1/0)'),
                                                    ('SS', 'Cumulatief: som van team totaal elke ronde'),
                                                    ('F1', 'Formule 1 systeem (10/8/6/5/4/3/2/1)')], default='2P', max_length=2)),
                ('einde_teams_aanmaken', models.DateField(default='2001-01-01')),
            ],
        ),
        migrations.CreateModel(
            name='DeelcompetitieRonde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_nr', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=40)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbcluster')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Wedstrijden.competitiewedstrijdenplan')),
            ],
        ),
        migrations.CreateModel(
            name='DeelcompetitieKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie Klasse Limiet',
                'verbose_name_plural': 'Deelcompetitie Klasse Limieten',
            },
        ),
        migrations.CreateModel(
            name='RegioCompetitieSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score1', models.PositiveIntegerField(default=0)),
                ('score2', models.PositiveIntegerField(default=0)),
                ('score3', models.PositiveIntegerField(default=0)),
                ('score4', models.PositiveIntegerField(default=0)),
                ('score5', models.PositiveIntegerField(default=0)),
                ('score6', models.PositiveIntegerField(default=0)),
                ('score7', models.PositiveIntegerField(default=0)),
                ('totaal', models.PositiveIntegerField(default=0)),
                ('laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('aantal_scores', models.PositiveSmallIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('bij_vereniging', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('klasse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
                ('schutterboog', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Schutter.schutterboog')),
                ('inschrijf_notitie', models.TextField(blank=True, default='')),
                ('inschrijf_voorkeur_dagdeel', models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"), ('MA', 'Maandag'), ('DI', 'Dinsdag'), ('WO', 'Woensdag'), ('DO', 'Donderdag'), ('VR', 'Vrijdag'), ('ZAT', 'Zaterdag'), ('ZAo', 'Zaterdagochtend'), ('ZAm', 'Zaterdagmiddag'), ('ZON', 'Zondag'), ('ZOo', 'Zondagochtend'), ('ZOm', 'Zondagmiddag'), ('WE', 'Weekend')], default='GN', max_length=3)),
                ('inschrijf_voorkeur_team', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
                ('alt_score1', models.PositiveIntegerField(default=0)),
                ('alt_score2', models.PositiveIntegerField(default=0)),
                ('alt_score3', models.PositiveIntegerField(default=0)),
                ('alt_score4', models.PositiveIntegerField(default=0)),
                ('alt_score5', models.PositiveIntegerField(default=0)),
                ('alt_score6', models.PositiveIntegerField(default=0)),
                ('alt_score7', models.PositiveIntegerField(default=0)),
                ('alt_totaal', models.PositiveIntegerField(default=0)),
                ('alt_laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('alt_aantal_scores', models.PositiveSmallIntegerField(default=0)),
                ('alt_gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_indiv', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team_mag_aangepast_worden', models.BooleanField(default=False)),
                ('inschrijf_gekozen_wedstrijden', models.ManyToManyField(blank=True, to='Wedstrijden.CompetitieWedstrijd')),
            ],
            options={
                'verbose_name': 'Regiocompetitie Schutterboog',
                'verbose_name_plural': 'Regiocompetitie Schuttersboog',
            },
        ),
        migrations.CreateModel(
            name='KampioenschapSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kampioen_label', models.CharField(blank=True, default='', max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                     to='NhbStructuur.nhbvereniging')),
                ('klasse',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
                ('schutterboog',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Schutter.schutterboog')),
                ('bevestiging_gevraagd_op', models.DateTimeField(blank=True, null=True)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('deelname',
                 models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?',
                                  max_length=1)),
            ],
            options={
                'verbose_name': 'Kampioenschap Schutterboog',
                'verbose_name_plural': 'Kampioenschap Schuttersboog',
            },
        ),
        migrations.CreateModel(
            name='KampioenschapMutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('deelnemer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                to='Competitie.kampioenschapschutterboog')),
                ('cut_nieuw', models.PositiveSmallIntegerField(default=0)),
                ('cut_oud', models.PositiveSmallIntegerField(default=0)),
                ('deelcompetitie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                                     to='Competitie.deelcompetitie')),
                ('klasse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                             to='Competitie.competitieklasse')),
            ],
            options={
                'verbose_name': 'Kampioenschap Mutatie',
                'verbose_name_plural': 'Kampioenschap Mutaties',
            },
        ),
        migrations.CreateModel(
            name='RegiocompetitieTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('klasse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
                ('gekoppelde_schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
            ],
        ),
        migrations.CreateModel(
            name='RegiocompetitieTeamPoule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(default='', max_length=100)),
                ('deelcompetitie',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('teams', models.ManyToManyField(blank=True, to='Competitie.RegiocompetitieTeam')),
            ],
        ),
        migrations.CreateModel(
            name='RegiocompetitieRondeTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ronde_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_score', models.PositiveSmallIntegerField(default=0)),
                ('team_punten', models.PositiveSmallIntegerField(default=0)),
                ('schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('team',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.regiocompetitieteam')),
            ],
        ),
        migrations.CreateModel(
            name='KampioenschapTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('klasse',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Competitie.competitieklasse')),
                ('schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                 to='NhbStructuur.nhbvereniging')),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_scorehist', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Score.scorehist')),
                ('hoogste_mutatie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Competitie.kampioenschapmutatie')),
            ],
        ),
        migrations.RunPython(init_taken),
    ]

# end of file
