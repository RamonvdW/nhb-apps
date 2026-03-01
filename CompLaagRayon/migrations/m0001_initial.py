# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

DEEL_RK = 'RK'


def do_migrate(apps, _):

    kamp2new = dict()       # [Kampioenschap.pk] --> KampRK
    deelnemer2new = dict()  # [KampioenschapSporterBoog.pk] --> DeelnemerRK

    # Kampioenschap --> KampRK
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kampioenschap_klas = apps.get_model('Competitie', 'Kampioenschap')
        kamp_rk_klas = apps.get_model('CompLaagRayon', 'KampRK')

        for deelkamp in (kampioenschap_klas
                              .objects
                              .filter(deel=DEEL_RK)
                              .select_related('competitie',
                                              'rayon',
                                              'functie')):

            kamp_rk = kamp_rk_klas.objects.create(
                            competitie=deelkamp.competitie,
                            rayon=deelkamp.rayon,
                            functie=deelkamp.functie,
                            is_afgesloten=deelkamp.is_afgesloten,
                            heeft_deelnemerslijst=deelkamp.heeft_deelnemerslijst)

            kamp2new[deelkamp.pk] = kamp_rk

            # migreer de RK matches
            kamp_rk.matches.set(deelkamp.rk_bk_matches.all())
            deelkamp.rk_bk_matches.clear()
        # for

    # KampioenschapSporterBoog (voor deel=DEEL_RK) --> DeelnemerRK
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kampioenschapsporterboog_klas = apps.get_model('Competitie', 'KampioenschapSporterBoog')
        deelnemer_rk_klas = apps.get_model('CompLaagRayon', 'DeelnemerRK')

        for deelnemer in (kampioenschapsporterboog_klas
                          .objects
                          .filter(kampioenschap__deel=DEEL_RK)
                          .select_related('kampioenschap',
                                          'sporterboog',
                                          'indiv_klasse',
                                          'indiv_klasse_volgende_ronde',
                                          'bij_vereniging')):

            deelnemer_rk = deelnemer_rk_klas.objects.create(
                                oude_pk=deelnemer.pk,
                                kamp=kamp2new[deelnemer.kampioenschap.pk],
                                sporterboog=deelnemer.sporterboog,
                                indiv_klasse=deelnemer.indiv_klasse,
                                indiv_klasse_volgende_ronde=deelnemer.indiv_klasse_volgende_ronde,
                                bij_vereniging=deelnemer.bij_vereniging,
                                kampioen_label=deelnemer.kampioen_label,
                                volgorde=deelnemer.volgorde,
                                rank=deelnemer.rank,
                                bevestiging_gevraagd_op=deelnemer.bevestiging_gevraagd_op,
                                deelname=deelnemer.deelname,
                                gemiddelde=deelnemer.gemiddelde,
                                gemiddelde_scores=deelnemer.gemiddelde_scores,
                                result_score_1=deelnemer.result_score_1,
                                result_score_2=deelnemer.result_score_2,
                                result_counts=deelnemer.result_counts,
                                result_rank=deelnemer.result_rank,
                                result_volgorde=deelnemer.result_volgorde,
                                logboek=deelnemer.logboek)

            deelnemer2new[deelnemer.pk] = deelnemer_rk
        # for

    # KampioenschapTeam --> TeamRK
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kampioenschapteam_klas = apps.get_model('Competitie', 'KampioenschapTeam')
        team_rk_klas = apps.get_model('CompLaagRayon', 'TeamRK')

        for team in (kampioenschapteam_klas
                     .objects
                     .filter(kampioenschap__deel=DEEL_RK)
                     .prefetch_related('tijdelijke_leden',
                                       'feitelijke_leden',
                                       'gekoppelde_leden')
                     .select_related('vereniging',
                                     'team_type',
                                     'team_klasse',
                                     'team_klasse_volgende_ronde')):

            team_rk = team_rk_klas.objects.create(
                            kamp=kamp2new[team.kampioenschap.pk],
                            vereniging=team.vereniging,
                            volg_nr=team.volg_nr,
                            team_type=team.team_type,
                            team_naam=team.team_naam,
                            deelname=team.deelname,
                            is_reserve=team.is_reserve,
                            aanvangsgemiddelde=team.aanvangsgemiddelde,
                            volgorde=team.volgorde,
                            rank=team.rank,
                            team_klasse=team.team_klasse,
                            team_klasse_volgende_ronde=team.team_klasse_volgende_ronde,
                            result_rank=team.result_rank,
                            result_volgorde=team.result_volgorde,
                            result_teamscore=team.result_teamscore,
                            result_shootoff_str=team.result_shootoff_str)

            # tijdelijke leden overzetten (RegiocompetitieSporterBoog)
            team_rk.tijdelijke_leden.set(team.tijdelijke_leden.all())
            team.tijdelijke_leden.clear()

            # gekoppelde_leden overzetten (KampioenschapSporterBoog --> DeelnemerRK)
            nieuw = list()
            for deelnemer in team.gekoppelde_leden.all():
                nieuw.append(deelnemer2new[deelnemer.pk])
            # for
            team_rk.gekoppelde_leden.set(nieuw)
            team.gekoppelde_leden.clear()

            # feitelijke_leden overzetten (KampioenschapSporterBoog --> DeelnemerRK)
            nieuw = list()
            for deelnemer in team.feitelijke_leden.all():
                nieuw.append(deelnemer2new[deelnemer.pk])
            # for
            team_rk.feitelijke_leden.set(nieuw)
            team.feitelijke_leden.clear()
        # for

    # KampioenschapIndivKlasseLimiet --> CutBK
    if True:
        limiet_klas = apps.get_model('Competitie', 'KampioenschapIndivKlasseLimiet')
        cut_klas = apps.get_model('CompLaagRayon', 'CutRK')

        bulk = list()
        for limiet in limiet_klas.objects.filter(kampioenschap__deel=DEEL_RK):
            bulk.append(
                cut_klas(
                    kamp=kamp2new[limiet.kampioenschap.pk],
                    indiv_klasse=limiet.indiv_klasse,
                    limiet=limiet.limiet)
            )
        # for
        cut_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0062_squashed'),
        ('Competitie', 'm0121_team_result_shootoff'),
        ('Functie', 'm0028_squashed'),
        ('Geo', 'm0002_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='KampRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('heeft_deelnemerslijst', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('functie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Functie.functie')),
                ('matches', models.ManyToManyField(blank=True, to='Competitie.competitiematch')),
                ('rayon', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Geo.rayon')),
            ],
            options={
                'verbose_name': 'KampRK',
                'ordering': ['competitie__afstand', 'rayon__rayon_nr'],
            },
        ),
        migrations.CreateModel(
            name='DeelnemerRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oude_pk', models.BigIntegerField(default=0)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('gemiddelde_scores', models.CharField(blank=True, default='', max_length=24)),
                ('kampioen_label', models.CharField(blank=True, default='', max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('bevestiging_gevraagd_op', models.DateTimeField(blank=True, null=True)),
                ('deelname', models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?', max_length=1)),
                ('result_score_1', models.PositiveSmallIntegerField(default=0)),
                ('result_score_2', models.PositiveSmallIntegerField(default=0)),
                ('result_counts', models.CharField(blank=True, default='', max_length=20)),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_volgorde', models.PositiveSmallIntegerField(default=99)),
                ('logboek', models.TextField(blank=True)),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
                ('indiv_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='deelnemer_rk_indiv_klasse', to='Competitie.competitieindivklasse')),
                ('indiv_klasse_volgende_ronde', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='deelnemer_rk_indiv_klasse_volgende_ronde', to='Competitie.competitieindivklasse')),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRayon.kamprk')),
            ],
            options={
                'verbose_name': 'DeelnemerRK',
                'verbose_name_plural': 'DeelnemersRK',
            },
        ),
        migrations.CreateModel(
            name='TeamRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('deelname', models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?', max_length=1)),
                ('is_reserve', models.BooleanField(default=False)),
                ('aanvangsgemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_volgorde', models.PositiveSmallIntegerField(default=0)),
                ('result_teamscore', models.PositiveSmallIntegerField(default=0)),
                ('result_shootoff_str', models.CharField(blank=True, default='', max_length=20)),
                ('feitelijke_leden', models.ManyToManyField(blank=True, related_name='teamrk_feitelijke_leden', to='CompLaagRayon.deelnemerrk')),
                ('gekoppelde_leden', models.ManyToManyField(blank=True, related_name='teamrk_gekoppelde_leden', to='CompLaagRayon.deelnemerrk')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRayon.kamprk')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teamrk_team_klasse', to='Competitie.competitieteamklasse')),
                ('team_klasse_volgende_ronde', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teamrk_team_klasse_volgende_ronde', to='Competitie.competitieteamklasse')),
                ('team_type', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('tijdelijke_leden', models.ManyToManyField(blank=True, related_name='teamrk_tijdelijke_leden', to='Competitie.regiocompetitiesporterboog')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'TeamRK',
                'verbose_name_plural': 'TeamsRK',
            },
        ),
        migrations.CreateModel(
            name='CutRK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('indiv_klasse',
                 models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagRayon.kamprk')),
            ],
            options={
                'verbose_name': 'Cut RK',
                'verbose_name_plural': 'Cuts RK',
            },
        ),
        migrations.AddIndex(
            model_name='deelnemerrk',
            index=models.Index(fields=['-gemiddelde'], name='CompLaagRay_gemidde_664c17_idx'),
        ),
        migrations.AddIndex(
            model_name='deelnemerrk',
            index=models.Index(fields=['volgorde'], name='CompLaagRay_volgord_cf0c20_idx'),
        ),
        migrations.AddIndex(
            model_name='deelnemerrk',
            index=models.Index(fields=['rank'], name='CompLaagRay_rank_61f5b1_idx'),
        ),
        migrations.AddIndex(
            model_name='deelnemerrk',
            index=models.Index(fields=['volgorde', '-gemiddelde'], name='CompLaagRay_volgord_c5f6d5_idx'),
        ),
        migrations.RunPython(do_migrate, reverse_code=migrations.RunPython.noop),
    ]

# end of file
