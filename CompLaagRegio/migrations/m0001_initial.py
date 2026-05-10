# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_uit_competitie(apps, _):
    """ Migreer de database tabellen van Competitie naar CompLaagRegio """

    regiocompetitie_pk2regiocomp = dict()
    regiocompetitieteam_pk2regioteam = dict()
    regiocompetitiesporterboog_pk2regiodeelnemer = dict()

    # Regiocompetitie --> RegioComp
    if True:
        print(' Regiocomp', end='')
        regiocompetitie_klas = apps.get_model('Competitie', 'Regiocompetitie')
        regiocomp_klas = apps.get_model('CompLaagRegio', 'RegioComp')

        count = 0
        for obj in (regiocompetitie_klas
                    .objects
                    .select_related('competitie',
                                    'regio',
                                    'functie')
                    .all()):

            new_obj = regiocomp_klas.objects.create(
                            competitie=obj.competitie,
                            regio=obj.regio,
                            functie=obj.functie,
                            is_afgesloten=obj.is_afgesloten,
                            inschrijf_methode=obj.inschrijf_methode,
                            toegestane_dagdelen=obj.toegestane_dagdelen,
                            regio_organiseert_teamcompetitie=obj.regio_organiseert_teamcompetitie,
                            regio_heeft_vaste_teams=obj.regio_heeft_vaste_teams,
                            begin_fase_D=obj.begin_fase_D,
                            regio_team_punten_model=obj.regio_team_punten_model,
                            huidige_team_ronde=obj.huidige_team_ronde)

            regiocompetitie_pk2regiocomp[obj.pk] = new_obj

            count += 1
        # for
        print(' %d' % count, end='')

    # RegiocompetitieRonde --> RegioRonde
    if True:
        print(' Rondes', end='')
        regiocompetitieronde_klas = apps.get_model('Competitie', 'RegiocompetitieRonde')
        regioronde_klas = apps.get_model('CompLaagRegio', 'RegioRonde')

        count = 0
        for obj in (regiocompetitieronde_klas
                    .objects
                    .select_related('regiocompetitie',
                                    'cluster')
                    .prefetch_related('matches')
                    .all()):

            regiocomp = regiocompetitie_pk2regiocomp[obj.regiocompetitie.pk]

            new_obj = regioronde_klas.objects.create(
                            regiocomp=regiocomp,
                            cluster=obj.cluster,
                            week_nr=obj.week_nr,
                            beschrijving=obj.beschrijving)

            new_obj.matches.set(obj.matches.all())

            count += 1
        # for
        print(' %d' % count, end='')

    # RegiocompetitieSporterBoog --> RegioDeelnemer
    if True:
        print(' Deelnemers', end='')
        regiocompetitiesporterboog_klas = apps.get_model('Competitie', 'RegiocompetitieSporterBoog')
        regiodeelnemer_klas = apps.get_model('CompLaagRegio', 'RegioDeelnemer')

        count = 0
        for obj in (regiocompetitiesporterboog_klas
                    .objects
                    .select_related('regiocompetitie',
                                    'sporterboog',
                                    'indiv_klasse',
                                    'bij_vereniging',
                                    'aangemeld_door')
                    .prefetch_related('scores',
                                      'inschrijf_gekozen_matches')
                    .all()):

            regiocomp = regiocompetitie_pk2regiocomp[obj.regiocompetitie.pk]

            new_obj = regiodeelnemer_klas.objects.create(
                            regiocomp=regiocomp,
                            sporterboog=obj.sporterboog,
                            bij_vereniging=obj.bij_vereniging,
                            indiv_klasse=obj.indiv_klasse,
                            ag_voor_indiv=obj.ag_voor_indiv,
                            ag_voor_team=obj.ag_voor_team,
                            ag_voor_team_mag_aangepast_worden=obj.ag_voor_team_mag_aangepast_worden,
                            inschrijf_voorkeur_team=obj.inschrijf_voorkeur_team,
                            inschrijf_voorkeur_rk_bk=obj.inschrijf_voorkeur_rk_bk,
                            inschrijf_voorkeur_dagdeel=obj.inschrijf_voorkeur_dagdeel,
                            inschrijf_notitie=obj.inschrijf_notitie,
                            score1=obj.score1,
                            score2=obj.score2,
                            score3=obj.score3,
                            score4=obj.score4,
                            score5=obj.score5,
                            score6=obj.score6,
                            score7=obj.score7,
                            totaal=obj.totaal,
                            aantal_scores=obj.aantal_scores,
                            laagste_score_nr=obj.laagste_score_nr,
                            gemiddelde=obj.gemiddelde,
                            gemiddelde_begin_team_ronde=obj.gemiddelde_begin_team_ronde,
                            aangemeld_door=obj.aangemeld_door,
                            logboekje=obj.logboekje,
                            wanneer_aangemeld=obj.wanneer_aangemeld)

            new_obj.inschrijf_gekozen_matches.set(obj.inschrijf_gekozen_matches.all())
            new_obj.scores.set(obj.scores.all())

            regiocompetitiesporterboog_pk2regiodeelnemer[obj.pk] = new_obj

            count += 1
        # for
        print(' %d' % count, end='')

    # RegiocompetitieTeam --> RegioTeam
    if True:
        print(' Teams', end='')
        regiocompetiteteam_klas = apps.get_model('Competitie', 'RegiocompetitieTeam')
        regioteam_klas = apps.get_model('CompLaagRegio', 'RegioTeam')

        count = 0
        for obj in (regiocompetiteteam_klas
                    .objects
                    .select_related('regiocompetitie',
                                    'vereniging',
                                    'team_type',
                                    'team_klasse')
                    .prefetch_related('leden')
                    .all()):

            regiocomp = regiocompetitie_pk2regiocomp[obj.regiocompetitie.pk]

            new_obj = regioteam_klas.objects.create(
                            regiocomp=regiocomp,
                            vereniging=obj.vereniging,
                            volg_nr=obj.volg_nr,
                            team_type=obj.team_type,
                            team_naam=obj.team_naam,
                            team_klasse=obj.team_klasse,
                            aanvangsgemiddelde=obj.aanvangsgemiddelde)

            new_leden = [regiocompetitiesporterboog_pk2regiodeelnemer[lid.pk]
                         for lid in obj.leden.all()]
            new_obj.leden.set(new_leden)

            regiocompetitieteam_pk2regioteam[obj.pk] = new_obj

            count += 1
        # for
        print(' %d' % count, end='')

    # RegiocompetitieTeamPoule --> RegioPoule
    if True:
        print(' Poules', end='')
        regiocompetitieteampoule_klas = apps.get_model('Competitie', 'RegiocompetitieTeamPoule')
        regiopoule_klas = apps.get_model('CompLaagRegio', 'RegioPoule')

        count = 0
        for obj in (regiocompetitieteampoule_klas
                    .objects
                    .select_related('regiocompetitie')
                    .prefetch_related('teams')
                    .all()):

            regiocomp = regiocompetitie_pk2regiocomp[obj.regiocompetitie.pk]

            new_obj = regiopoule_klas.objects.create(
                            regiocomp=regiocomp,
                            beschrijving=obj.beschrijving)

            new_teams = [regiocompetitieteam_pk2regioteam[team.pk]
                         for team in obj.teams.all()]
            new_obj.teams.set(new_teams)

            count += 1
        # for
        print(' %d' % count, end='')

    # RegiocompetitieRondeTeam --> RegioRondeTeam
    if True:
        print(' RondeTeams', end='')
        regiocompetitierondeteam_klas = apps.get_model('Competitie', 'RegiocompetitieRondeTeam')
        regiorondeteam_klas = apps.get_model('CompLaagRegio', 'RegioRondeTeam')

        count = 0
        for obj in (regiocompetitierondeteam_klas
                    .objects
                    .select_related('team')
                    .prefetch_related('deelnemers_geselecteerd',
                                      'deelnemers_feitelijk',
                                      'scores_feitelijk',
                                      'scorehist_feitelijk')
                    .all()):

            team = regiocompetitieteam_pk2regioteam[obj.team.pk]

            new_obj = regiorondeteam_klas.objects.create(
                            team=team,
                            ronde_nr=obj.ronde_nr,
                            team_score=obj.team_score,
                            team_punten=obj.team_punten,
                            logboek=obj.logboek)

            new_obj.scores_feitelijk.set(obj.scores_feitelijk.all())
            new_obj.scorehist_feitelijk.set(obj.scorehist_feitelijk.all())

            new_deelnemers = [regiocompetitiesporterboog_pk2regiodeelnemer[deelnemer.pk]
                              for deelnemer in obj.deelnemers_geselecteerd.all()]
            new_obj.deelnemers_geselecteerd.set(new_deelnemers)

            new_deelnemers = [regiocompetitiesporterboog_pk2regiodeelnemer[deelnemer.pk]
                              for deelnemer in obj.deelnemers_feitelijk.all()]
            new_obj.deelnemers_feitelijk.set(new_deelnemers)

            count += 1
        # for
        print(' %d' % count, end='')


class Migration(migrations.Migration):

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0062_squashed'),
        ('Competitie', 'm0123_kamp_migratie'),
        ('Functie', 'm0028_squashed'),
        ('Geo', 'm0002_squashed'),
        ('Score', 'm0021_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Vereniging', 'm0007_squashed'),
        ('Account', 'm0032_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='RegioComp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('inschrijf_methode', models.CharField(choices=[('1', 'Kies wedstrijden'),
                                                                ('2', 'Naar locatie wedstrijdklasse'),
                                                                ('3', 'Voorkeur dagdelen')],
                                                       default='2', max_length=1)),
                ('toegestane_dagdelen', models.CharField(blank=True, default='', max_length=40)),
                ('regio_organiseert_teamcompetitie', models.BooleanField(default=True)),
                ('regio_heeft_vaste_teams', models.BooleanField(default=True)),
                ('begin_fase_D', models.DateField(default='2001-01-01')),
                ('regio_team_punten_model', models.CharField(choices=[('2P', 'Twee punten systeem (2/1/0)'),
                                                                      ('SS', 'Cumulatief: som van team totaal elke ronde'),
                                                                      ('F1', 'Formule 1 systeem (10/8/6/5/4/3/2/1)')],
                                                             default='2P', max_length=2)),
                ('huidige_team_ronde', models.PositiveSmallIntegerField(default=0)),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('functie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Functie.functie')),
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Geo.regio')),
            ],
            options={
                'verbose_name': 'Regio competitie',
            },
        ),
        migrations.CreateModel(
            name='RegioDeelnemer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_aangemeld', models.DateField(auto_now_add=True)),
                ('ag_voor_indiv', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('ag_voor_team_mag_aangepast_worden', models.BooleanField(default=False)),
                ('score1', models.PositiveIntegerField(default=0)),
                ('score2', models.PositiveIntegerField(default=0)),
                ('score3', models.PositiveIntegerField(default=0)),
                ('score4', models.PositiveIntegerField(default=0)),
                ('score5', models.PositiveIntegerField(default=0)),
                ('score6', models.PositiveIntegerField(default=0)),
                ('score7', models.PositiveIntegerField(default=0)),
                ('totaal', models.PositiveIntegerField(default=0)),
                ('aantal_scores', models.PositiveSmallIntegerField(default=0)),
                ('laagste_score_nr', models.PositiveIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('gemiddelde_begin_team_ronde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('inschrijf_voorkeur_team', models.BooleanField(default=False)),
                ('inschrijf_voorkeur_rk_bk', models.BooleanField(default=True)),
                ('inschrijf_notitie', models.TextField(blank=True, default='')),
                ('inschrijf_voorkeur_dagdeel', models.CharField(choices=[('GN', 'Geen voorkeur'), ('AV', "'s Avonds"),
                                                                         ('MA', 'Maandag'), ('MAa', 'Maandagavond'),
                                                                         ('DI', 'Dinsdag'), ('DIa', 'Dinsdagavond'),
                                                                         ('WO', 'Woensdag'), ('WOa', 'Woensdagavond'),
                                                                         ('DO', 'Donderdag'), ('DOa', 'Donderdagavond'),
                                                                         ('VR', 'Vrijdag'), ('VRa', 'Vrijdagavond'),
                                                                         ('ZAT', 'Zaterdag'), ('ZAo', 'Zaterdagochtend'),
                                                                         ('ZAm', 'Zaterdagmiddag'),
                                                                         ('ZAa', 'Zaterdagavond'), ('ZON', 'Zondag'),
                                                                         ('ZOo', 'Zondagochtend'),
                                                                         ('ZOm', 'Zondagmiddag'),
                                                                         ('ZOa', 'Zondagavond'),
                                                                         ('WE', 'Weekend')],
                                                                default='GN', max_length=3)),
                ('logboekje', models.TextField(blank=True, default='')),
                ('aangemeld_door', models.ForeignKey(blank=True, null=True,
                                                     on_delete=models.deletion.SET_NULL, to='Account.account')),
                ('bij_vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
                ('indiv_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
                ('inschrijf_gekozen_matches', models.ManyToManyField(blank=True, to='Competitie.competitiematch')),
                ('regiocomp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRegio.regiocomp')),
                ('scores', models.ManyToManyField(blank=True, to='Score.score')),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
            ],
            options={
                'verbose_name': 'Deelnemer',
            },
        ),
        migrations.CreateModel(
            name='RegioRonde',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_nr', models.PositiveSmallIntegerField()),
                ('beschrijving', models.CharField(max_length=40)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.cluster')),
                ('matches', models.ManyToManyField(blank=True, to='Competitie.competitiematch')),
                ('regiocomp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRegio.regiocomp')),
            ],
            options={
                'verbose_name': 'Ronde',
            },
        ),
        migrations.CreateModel(
            name='RegioTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('leden', models.ManyToManyField(blank=True, to='CompLaagRegio.regiodeelnemer')),
                ('regiocomp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRegio.regiocomp')),
                ('team_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieteamklasse',
                                                  blank=True, null=True)),
                ('team_type', models.ForeignKey(on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('vereniging', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'Team',
                'ordering': ['vereniging__ver_nr', 'volg_nr'],
            },
        ),
        migrations.CreateModel(
            name='RegioRondeTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ronde_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_score', models.PositiveSmallIntegerField(default=0)),
                ('team_punten', models.PositiveSmallIntegerField(default=0)),
                ('logboek', models.TextField(blank=True)),
                ('deelnemers_feitelijk', models.ManyToManyField(blank=True, related_name='regiorondeteam_feitelijk',
                                                                to='CompLaagRegio.regiodeelnemer')),
                ('deelnemers_geselecteerd', models.ManyToManyField(blank=True, related_name='regiorondeteam_geselecteerd',
                                                                   to='CompLaagRegio.regiodeelnemer')),
                ('scorehist_feitelijk', models.ManyToManyField(blank=True, related_name='regiorondeteam_feitelijk',
                                                               to='Score.scorehist')),
                ('scores_feitelijk', models.ManyToManyField(blank=True, related_name='regiorondeteam_feitelijk',
                                                            to='Score.score')),
                ('team', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRegio.regioteam')),
            ],
            options={
                'verbose_name': 'Ronde team',
            },
        ),
        migrations.CreateModel(
            name='RegioPoule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beschrijving', models.CharField(default='', max_length=100)),
                ('regiocomp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRegio.regiocomp')),
                ('teams', models.ManyToManyField(blank=True, to='CompLaagRegio.regioteam')),
            ],
            options={
                'verbose_name': 'Poule',
            },
        ),
        migrations.AddIndex(
            model_name='regiodeelnemer',
            index=models.Index(fields=['aantal_scores'], name='CompLaagReg_aantal__28cb85_idx'),
        ),
        migrations.AddIndex(
            model_name='regiodeelnemer',
            index=models.Index(fields=['-gemiddelde'], name='CompLaagReg_gemidde_3428f4_idx'),
        ),
        migrations.AddIndex(
            model_name='regiodeelnemer',
            index=models.Index(fields=['aantal_scores', 'regiocomp'], name='CompLaagReg_aantal__ff7116_idx'),
        ),
        migrations.RunPython(migreer_uit_competitie, reverse_code=migrations.RunPython.noop),
    ]

# end of file
