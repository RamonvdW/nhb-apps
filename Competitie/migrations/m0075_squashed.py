# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models


def init_taken(apps, _):
    """ Maak de enige tabel regel aan die gebruikt wordt door het cron job
        regiocomp_upd_tussenstand.
    """
    # haal de klassen op die van toepassing zijn tijdens deze migratie
    taken_klas = apps.get_model('Competitie', 'CompetitieTaken')

    taken_klas().save()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # replaces = [('Competitie', 'm0065_squashed'),
    #             ('Competitie', 'm0066_competitie_typen'),
    #             ('Competitie', 'm0067_klasse_split_1'),
    #             ('Competitie', 'm0068_klasse_split_2'),
    #             ('Competitie', 'm0069_klasse_split_3'),
    #             ('Competitie', 'm0070_klasse_split_4'),
    #             ('Competitie', 'm0071_matches'),
    #             ('Competitie', 'm0072_limiet_split'),
    #             ('Competitie', 'm0073_inschrijf_voorkeur_rk_bk'),
    #             ('Competitie', 'm0074_ingeschreven_door')]

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0021_squashed'),
        ('BasisTypen', 'm0049_squashed'),
        ('Functie', 'm0012_squashed'),
        ('NhbStructuur', 'm0027_squashed'),
        ('Score', 'm0017_squashed'),
        ('Sporter', 'm0010_squashed'),
        ('Wedstrijden', 'm0023_squashed'),
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
                ('datum_klassengrenzen_rk_bk_teams', models.DateField()),
                ('rk_eerste_wedstrijd', models.DateField()),
                ('rk_laatste_wedstrijd', models.DateField()),
                ('klassengrenzen_vastgesteld', models.BooleanField(default=False)),
                ('klassengrenzen_vastgesteld_rk_bk', models.BooleanField(default=False)),
                ('aantal_scores_voor_rk_deelname', models.PositiveSmallIntegerField(default=6)),
                ('rk_afgelast_bericht', models.TextField(blank=True)),
                ('rk_is_afgelast', models.BooleanField(default=False)),
                ('bk_afgelast_bericht', models.TextField(blank=True)),
                ('bk_is_afgelast', models.BooleanField(default=False)),
                ('boogtypen', models.ManyToManyField(to='BasisTypen.BoogType')),
                ('teamtypen', models.ManyToManyField(to='BasisTypen.TeamType')),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieTeamKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volgorde', models.PositiveIntegerField()),
                ('beschrijving', models.CharField(max_length=80)),
                ('team_afkorting', models.CharField(max_length=3)),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('is_voor_teams_rk_bk', models.BooleanField(default=False)),
                ('blazoen1_regio', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('blazoen2_regio', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('blazoen_rk_bk', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('boog_typen', models.ManyToManyField(to='BasisTypen.BoogType')),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('team_type', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
            ],
            options={
                'verbose_name': 'Competitie team klasse',
                'verbose_name_plural': 'Competitie team klassen',
            },
        ),
        migrations.AddIndex(
            model_name='competitieteamklasse',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_054e8a_idx'),
        ),
        migrations.CreateModel(
            name='CompetitieIndivKlasse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(max_length=80)),
                ('volgorde', models.PositiveIntegerField()),
                ('min_ag', models.DecimalField(decimal_places=3, max_digits=5)),
                ('is_onbekend', models.BooleanField(default=False)),
                ('is_aspirant_klasse', models.BooleanField(default=False)),
                ('is_voor_rk_bk', models.BooleanField(default=False)),
                ('blazoen1_regio', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('blazoen2_regio', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('blazoen_rk_bk', models.CharField(
                    choices=[('40', '40cm'), ('60', '60cm'), ('4S', '60cm 4-spot'), ('DT', 'Dutch Target')],
                    default='40', max_length=2)),
                ('boogtype', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.boogtype')),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('leeftijdsklassen', models.ManyToManyField(to='BasisTypen.LeeftijdsKlasse')),
            ],
            options={
                'verbose_name': 'Competitie indiv klasse',
                'verbose_name_plural': 'Competitie indiv klassen',
            },
        ),
        migrations.AddIndex(
            model_name='competitieindivklasse',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_476d31_idx'),
        ),
        migrations.CreateModel(
            name='CompetitieMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('beschrijving', models.CharField(blank=True, max_length=100)),
                ('datum_wanneer', models.DateField()),
                ('tijd_begin_wedstrijd', models.TimeField()),
                ('indiv_klassen', models.ManyToManyField(blank=True, to='Competitie.CompetitieIndivKlasse')),
                ('locatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijdlocatie')),
                ('team_klassen', models.ManyToManyField(blank=True, to='Competitie.CompetitieTeamKlasse')),
                ('uitslag', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Score.uitslag')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
            ],
            options={
                'verbose_name': 'Competitie Match',
                'verbose_name_plural': 'Competitie Matches',
            },
        ),
        migrations.CreateModel(
            name='DeelCompetitie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('laag', models.CharField(choices=[('Regio', 'Regiocompetitie'), ('RK', 'Rayoncompetitie'), ('BK', 'Bondscompetitie')], max_length=5)),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('nhb_rayon', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbrayon')),
                ('nhb_regio', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
                ('functie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Functie.functie')),
                ('inschrijf_methode', models.CharField(choices=[('1', 'Kies wedstrijden'), ('2', 'Naar locatie wedstrijdklasse'), ('3', 'Voorkeur dagdelen')], default='2', max_length=1)),
                ('heeft_deelnemerslijst', models.BooleanField(default=False)),
                ('regio_heeft_vaste_teams', models.BooleanField(default=True)),
                ('regio_organiseert_teamcompetitie', models.BooleanField(default=True)),
                ('regio_team_punten_model', models.CharField(choices=[('2P', 'Twee punten systeem (2/1/0)'), ('SS', 'Cumulatief: som van team totaal elke ronde'), ('F1', 'Formule 1 systeem (10/8/6/5/4/3/2/1)')], default='2P', max_length=2)),
                ('einde_teams_aanmaken', models.DateField(default='2001-01-01')),
                ('toegestane_dagdelen', models.CharField(blank=True, default='', max_length=40)),
                ('huidige_team_ronde', models.PositiveSmallIntegerField(default=0)),
                ('rk_bk_matches', models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch')),
            ],
        ),
        migrations.CreateModel(
            name='DeelcompetitieRonde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_nr', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=40)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbcluster')),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('matches', models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch')),
            ],
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
                ('bij_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('inschrijf_notitie', models.TextField(blank=True, default='')),
                ('inschrijf_voorkeur_team', models.BooleanField(default=False)),
                ('scores', models.ManyToManyField(blank=True, to='Score.Score')),
                ('ag_voor_indiv', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team_mag_aangepast_worden', models.BooleanField(default=False)),
                ('inschrijf_gekozen_matches', models.ManyToManyField(blank=True, to='Competitie.CompetitieMatch')),
                ('inschrijf_voorkeur_dagdeel', models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"), ('MA', 'Maandag'), ('MAa', 'Maandagavond'), ('DI', 'Dinsdag'), ('DIa', 'Dinsdagavond'), ('WO', 'Woensdag'), ('WOa', 'Woensdagavond'), ('DO', 'Donderdag'), ('DOa', 'Donderdagavond'), ('VR', 'Vrijdag'), ('VRa', 'Vrijdagavond'), ('ZAT', 'Zaterdag'), ('ZAo', 'Zaterdagochtend'), ('ZAm', 'Zaterdagmiddag'), ('ZAa', 'Zaterdagavond'), ('ZON', 'Zondag'), ('ZOo', 'Zondagochtend'), ('ZOm', 'Zondagmiddag'), ('ZOa', 'Zondagavond'), ('WE', 'Weekend')], default='GN', max_length=3)),
                ('gemiddelde_begin_team_ronde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('inschrijf_voorkeur_rk_bk', models.BooleanField(default=True)),
                ('aangemeld_door', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('indiv_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
            ],
            options={
                'verbose_name': 'Regiocompetitie Schutterboog',
                'verbose_name_plural': 'Regiocompetitie Schuttersboog',
            },
        ),
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['aantal_scores'], name='Competitie__aantal__1682db_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['aantal_scores', 'deelcompetitie'], name='Competitie__aantal__409f0d_idx'),
        ),
        migrations.AddIndex(
            model_name='regiocompetitieschutterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_83a773_idx'),
        ),
        migrations.CreateModel(
            name='KampioenschapSchutterBoog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kampioen_label', models.CharField(blank=True, default='', max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('bevestiging_gevraagd_op', models.DateTimeField(blank=True, null=True)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('deelname', models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?', max_length=1)),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('regio_scores', models.CharField(blank=True, default='', max_length=24)),
                ('result_counts', models.CharField(blank=True, default='', max_length=20)),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_score_1', models.PositiveSmallIntegerField(default=0)),
                ('result_score_2', models.PositiveSmallIntegerField(default=0)),
                ('result_teamscore_1', models.PositiveSmallIntegerField(default=0)),
                ('result_teamscore_2', models.PositiveSmallIntegerField(default=0)),
                ('indiv_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
            ],
            options={
                'verbose_name': 'Kampioenschap Schutterboog',
                'verbose_name_plural': 'Kampioenschap Schuttersboog',
            },
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['-gemiddelde'], name='Competitie__gemidde_2899dc_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['volgorde'], name='Competitie__volgord_791c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['rank'], name='Competitie__rank_2f6fbf_idx'),
        ),
        migrations.AddIndex(
            model_name='kampioenschapschutterboog',
            index=models.Index(fields=['volgorde', '-gemiddelde'], name='Competitie__volgord_9cc75f_idx'),
        ),
        migrations.CreateModel(
            name='RegiocompetitieTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_type', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('gekoppelde_schutters', models.ManyToManyField(blank=True, to='Competitie.RegioCompetitieSchutterBoog')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
            options={
                'ordering': ['vereniging__ver_nr', 'volg_nr'],
            },
        ),
        migrations.CreateModel(
            name='RegiocompetitieTeamPoule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(default='', max_length=100)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
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
                ('team', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.regiocompetitieteam')),
                ('logboek', models.TextField(blank=True, max_length=1024)),
                ('deelnemers_feitelijk', models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Competitie.RegioCompetitieSchutterBoog')),
                ('deelnemers_geselecteerd', models.ManyToManyField(blank=True, related_name='teamronde_geselecteerd', to='Competitie.RegioCompetitieSchutterBoog')),
                ('scorehist_feitelijk', models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Score.ScoreHist')),
                ('scores_feitelijk', models.ManyToManyField(blank=True, related_name='teamronde_feitelijk', to='Score.Score')),
            ],
        ),
        migrations.CreateModel(
            name='KampioenschapTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbvereniging')),
                ('team_type', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('feitelijke_schutters', models.ManyToManyField(blank=True, related_name='kampioenschapteam_feitelijke_schutters', to='Competitie.KampioenschapSchutterBoog')),
                ('gekoppelde_schutters', models.ManyToManyField(blank=True, related_name='kampioenschapteam_gekoppelde_schutters', to='Competitie.KampioenschapSchutterBoog')),
                ('tijdelijke_schutters', models.ManyToManyField(blank=True, related_name='kampioenschapteam_tijdelijke_schutters', to='Competitie.RegioCompetitieSchutterBoog')),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_teamscore', models.PositiveSmallIntegerField(default=0)),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
        ),
        migrations.CreateModel(
            name='CompetitieMutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('mutatie', models.PositiveSmallIntegerField(default=0)),
                ('is_verwerkt', models.BooleanField(default=False)),
                ('door', models.CharField(default='', max_length=50)),
                ('cut_oud', models.PositiveSmallIntegerField(default=0)),
                ('cut_nieuw', models.PositiveSmallIntegerField(default=0)),
                ('deelcompetitie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('deelnemer', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.kampioenschapschutterboog')),
                ('competitie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('indiv_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
            options={
                'verbose_name': 'Competitie mutatie',
            },
        ),
        migrations.CreateModel(
            name='DeelcompetitieTeamKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie TeamKlasse Limiet',
                'verbose_name_plural': 'Deelcompetitie TeamKlasse Limieten',
            },
        ),
        migrations.CreateModel(
            name='DeelcompetitieIndivKlasseLimiet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('deelcompetitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.deelcompetitie')),
                ('indiv_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
            ],
            options={
                'verbose_name': 'Deelcompetitie IndivKlasse Limiet',
                'verbose_name_plural': 'Deelcompetitie IndivKlasse Limieten',
            },
        ),
        migrations.CreateModel(
            name='CompetitieTaken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoogste_scorehist', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Score.scorehist')),
                ('hoogste_mutatie', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Competitie.competitiemutatie')),
            ],
        ),
        migrations.RunPython(init_taken),
    ]

# end of file
