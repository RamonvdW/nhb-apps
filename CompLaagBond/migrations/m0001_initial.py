# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models

DEEL_BK = 'BK'


def do_migrate(apps, _):

    kamp2new = dict()       # [Kampioenschap.pk] --> KampBK

    # Kampioenschap --> KampBK
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kampioenschap_klas = apps.get_model('Competitie', 'Kampioenschap')
        kamp_bk_klas = apps.get_model('CompLaagBond', 'KampBK')

        for deelkamp in kampioenschap_klas.objects.filter(deel=DEEL_BK):

            kamp_bk = kamp_bk_klas.objects.create(
                            competitie=deelkamp.competitie,
                            functie=deelkamp.functie,
                            is_afgesloten=deelkamp.is_afgesloten,
                            heeft_deelnemerslijst=deelkamp.heeft_deelnemerslijst)

            kamp2new[deelkamp.pk] = kamp_bk

            # migreer de matches
            kamp_bk.matches.set(deelkamp.rk_bk_matches.all())
            deelkamp.rk_bk_matches.clear()
        # for

    # KampioenschapSporterBoog (voor deel=DEEL_BK) --> DeelnemerBK
    if True:
        kampioenschapsporterboog_klas = apps.get_model('Competitie', 'KampioenschapSporterBoog')
        deelnemer_bk_klas = apps.get_model('CompLaagBond', 'DeelnemerBK')

        for deelnemer in (kampioenschapsporterboog_klas
                          .objects
                          .filter(kampioenschap__deel=DEEL_BK)
                          .select_related('kampioenschap',
                                          'sporterboog',
                                          'indiv_klasse',
                                          'indiv_klasse_volgende_ronde',
                                          'bij_vereniging')):

            deelnemer_bk_klas.objects.create(
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
        # for

    # KampioenschapTeam --> TeamBK
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kampioenschapteam_klas = apps.get_model('Competitie', 'KampioenschapTeam')
        deelnemer_rk_klas = apps.get_model('CompLaagRayon', 'DeelnemerRK')
        team_bk_klas = apps.get_model('CompLaagBond', 'TeamBK')

        # haal alle DeelnemerRK records op (om te koppelen aan de teams)
        deelnemer2new = dict()  # [(RK) KampioenschapSporterBoog.pk] --> DeelnemerRK
        for deelnemer_rk in deelnemer_rk_klas.objects.all():
            deelnemer2new[deelnemer_rk.oude_pk] = deelnemer_rk
        # for

        # migreer elk team
        for team in (kampioenschapteam_klas
                     .objects
                     .filter(kampioenschap__deel=DEEL_BK)
                     .prefetch_related('gekoppelde_leden',
                                       'feitelijke_leden')
                     .select_related('vereniging',
                                     'team_type',
                                     'team_klasse',
                                     'team_klasse_volgende_ronde')):

            team_bk = team_bk_klas.objects.create(
                            kamp=kamp2new[team.kampioenschap.pk],
                            vereniging=team.vereniging,
                            volg_nr=team.volg_nr,
                            team_type=team.team_type,
                            team_naam=team.team_naam,
                            deelname=team.deelname,
                            is_reserve=team.is_reserve,
                            rk_score=round(team.aanvangsgemiddelde),        # bevat rk_score as-is
                            volgorde=team.volgorde,
                            rank=team.rank,
                            team_klasse=team.team_klasse,
                            team_klasse_volgende_ronde=team.team_klasse_volgende_ronde,
                            result_rank=team.result_rank,
                            result_volgorde=team.result_volgorde,
                            result_teamscore=team.result_teamscore,
                            result_shootoff_str=team.result_shootoff_str)

            # gekoppelde_leden overzetten (KampioenschapSporterBoog --> DeelnemerRK)
            nieuw = list()
            for deelnemer in team.gekoppelde_leden.all():
                nieuw.append(deelnemer2new[deelnemer.pk])
            # for
            team_bk.gekoppelde_leden.set(nieuw)
            team.gekoppelde_leden.clear()

            # feitelijke_leden overzetten (KampioenschapSporterBoog --> DeelnemerRK)
            nieuw = list()
            for deelnemer in team.feitelijke_leden.all():
                nieuw.append(deelnemer2new[deelnemer.pk])
            # for
            team_bk.feitelijke_leden.set(nieuw)
            team.feitelijke_leden.clear()
        # for

    # KampioenschapIndivKlasseLimiet --> CutBK
    if True:
        limiet_klas = apps.get_model('Competitie', 'KampioenschapIndivKlasseLimiet')
        cut_klas = apps.get_model('CompLaagBond', 'CutBK')

        bulk = list()
        for limiet in limiet_klas.objects.filter(kampioenschap__deel=DEEL_BK):
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
        ('CompLaagRayon', 'm0001_initial'),             # levert DeelnemerRK nodig voor TeamBK.feitelijke_leden
        ('Competitie', 'm0121_team_result_shootoff'),
        ('Functie', 'm0028_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Vereniging', 'm0007_squashed'),
    ]

    # migratie functie
    operations = [
        migrations.CreateModel(
            name='KampBK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_afgesloten', models.BooleanField(default=False)),
                ('heeft_deelnemerslijst', models.BooleanField(default=False)),
                ('competitie', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitie')),
                ('functie', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Functie.functie')),
                ('matches', models.ManyToManyField(blank=True, to='Competitie.competitiematch')),
            ],
            options={
                'verbose_name': 'KampBK',
                'ordering': ['competitie__afstand'],
            },
        ),
        migrations.CreateModel(
            name='TeamBK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volg_nr', models.PositiveSmallIntegerField(default=0)),
                ('team_naam', models.CharField(default='', max_length=50)),
                ('deelname', models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?', max_length=1)),
                ('is_reserve', models.BooleanField(default=False)),
                ('rk_score', models.PositiveSmallIntegerField(default=0)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_volgorde', models.PositiveSmallIntegerField(default=0)),
                ('result_teamscore', models.PositiveSmallIntegerField(default=0)),
                ('result_shootoff_str', models.CharField(blank=True, default='', max_length=20)),
                ('feitelijke_leden', models.ManyToManyField(blank=True, related_name='teambk_feitelijke_leden', to='CompLaagRayon.deelnemerrk')),
                ('gekoppelde_leden', models.ManyToManyField(blank=True, related_name='teambk_gekoppelde_leden', to='CompLaagRayon.deelnemerrk')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagBond.kampbk')),
                ('team_klasse', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teambk_team_klasse', to='Competitie.competitieteamklasse')),
                ('team_klasse_volgende_ronde', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teambk_team_klasse_volgende_ronde', to='Competitie.competitieteamklasse')),
                ('team_type', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='BasisTypen.teamtype')),
                ('vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
            ],
            options={
                'verbose_name': 'TeamBK',
                'verbose_name_plural': 'TeamsBK',
            },
        ),
        migrations.CreateModel(
            name='DeelnemerBK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kampioen_label', models.CharField(blank=True, default='', max_length=50)),
                ('volgorde', models.PositiveSmallIntegerField(default=0)),
                ('rank', models.PositiveSmallIntegerField(default=0)),
                ('bevestiging_gevraagd_op', models.DateTimeField(blank=True, null=True)),
                ('deelname', models.CharField(choices=[('?', 'Onbekend'), ('J', 'Bevestigd'), ('N', 'Afgemeld')], default='?', max_length=1)),
                ('gemiddelde', models.DecimalField(decimal_places=3, default=0.0, max_digits=5)),
                ('gemiddelde_scores', models.CharField(blank=True, default='', max_length=24)),
                ('result_score_1', models.PositiveSmallIntegerField(default=0)),
                ('result_score_2', models.PositiveSmallIntegerField(default=0)),
                ('result_counts', models.CharField(blank=True, default='', max_length=20)),
                ('result_rank', models.PositiveSmallIntegerField(default=0)),
                ('result_volgorde', models.PositiveSmallIntegerField(default=99)),
                ('logboek', models.TextField(blank=True)),
                ('bij_vereniging', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Vereniging.vereniging')),
                ('indiv_klasse', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='deelnemer_bk_indiv_klasse', to='Competitie.competitieindivklasse')),
                ('indiv_klasse_volgende_ronde', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='deelnemer_bk_indiv_klasse_volgende_ronde', to='Competitie.competitieindivklasse')),
                ('sporterboog', models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagBond.kampbk')),
            ],
            options={
                'verbose_name': 'DeelnemerBK',
                'verbose_name_plural': 'DeelnemersBK',
                'indexes': [models.Index(fields=['-gemiddelde'], name='CompLaagBon_gemidde_6eb15c_idx'), models.Index(fields=['volgorde'], name='CompLaagBon_volgord_da3a6e_idx'), models.Index(fields=['rank'], name='CompLaagBon_rank_4a0b60_idx'), models.Index(fields=['volgorde', '-gemiddelde'], name='CompLaagBon_volgord_d849eb_idx')],
            },
        ),
        migrations.CreateModel(
            name='CutBK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limiet', models.PositiveSmallIntegerField(default=24)),
                ('indiv_klasse',
                 models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitieindivklasse')),
                ('kamp', models.ForeignKey(on_delete=models.deletion.CASCADE, to='CompLaagBond.kampbk')),
            ],
            options={
                'verbose_name': 'Cut BK',
                'verbose_name_plural': 'Cuts BK',
            },
        ),
        migrations.RunPython(do_migrate, reverse_code=migrations.RunPython.noop),
    ]

# end of file
