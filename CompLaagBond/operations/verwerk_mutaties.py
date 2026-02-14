# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEEL_RK, DEEL_BK, DEELNAME_JA, DEELNAME_NEE, KAMP_RANK_BLANCO
from Competitie.models import (Competitie, CompetitieTeamKlasse, KampioenschapTeamKlasseLimiet,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from CompKampioenschap.operations import VerwerkCompKampMutaties


class VerwerkCompLaagBondMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

    def maak_deelnemerslijst_bk_indiv(self, comp: Competitie):
        # let op: deze methode wordt rechtstreeks aangeroepen vanuit VerwerkCompBeheerMutaties
        """ bepaal de individuele deelnemers van het BK
            per klasse zijn dit de rayonkampioenen (4x) aangevuld met de sporters met de hoogste kwalificatie scores
            iedereen die scores neergezet heeft in het RK komt in de lijst
        """

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan de BK indiv deelnemerslijst\n" % stamp_str

        if comp.is_indoor():
            aantal_pijlen = 2.0 * 30
        else:
            aantal_pijlen = 2.0 * 25

        deelkamp_bk = Kampioenschap.objects.get(deel=DEEL_BK, competitie=comp)

        # verwijder alle deelnemers van een voorgaande run
        KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk).delete()

        bulk = list()
        for kampioen in (KampioenschapSporterBoog
                         .objects
                         .filter(kampioenschap__competitie=comp,
                                 kampioenschap__deel=DEEL_RK,
                                 result_rank__lte=KAMP_RANK_BLANCO)
                         .exclude(deelname=DEELNAME_NEE)
                         .exclude(result_rank=0)
                         .select_related('kampioenschap',
                                         'kampioenschap__rayon',
                                         'indiv_klasse_volgende_ronde',
                                         'bij_vereniging',
                                         'sporterboog')):

            som_scores = kampioen.result_score_1 + kampioen.result_score_2
            gemiddelde = som_scores / aantal_pijlen

            if kampioen.result_score_1 > kampioen.result_score_2:
                gemiddelde_scores = "%03d%03d" % (kampioen.result_score_1, kampioen.result_score_2)
            else:
                gemiddelde_scores = "%03d%03d" % (kampioen.result_score_2, kampioen.result_score_1)

            # print('kampioen:', kampioen.result_rank, som_scores, gemiddelde_scores, "%.3f" % gemiddelde, kampioen)

            nieuw = KampioenschapSporterBoog(
                        kampioenschap=deelkamp_bk,
                        sporterboog=kampioen.sporterboog,
                        indiv_klasse=kampioen.indiv_klasse_volgende_ronde,
                        indiv_klasse_volgende_ronde=kampioen.indiv_klasse_volgende_ronde,
                        bij_vereniging=kampioen.bij_vereniging,
                        gemiddelde=gemiddelde,
                        gemiddelde_scores=gemiddelde_scores,
                        logboek=msg)

            if kampioen.result_rank == 1:
                nieuw.kampioen_label = 'Kampioen %s' % kampioen.kampioenschap.rayon.naam
                nieuw.deelname = DEELNAME_JA
                nieuw.logboek += '[%s] Deelname op Ja gezet, want kampioen RK\n' % stamp_str

            bulk.append(nieuw)

            if len(bulk) >= 250:
                KampioenschapSporterBoog.objects.bulk_create(bulk)
                bulk = list()
        # for

        if len(bulk):
            KampioenschapSporterBoog.objects.bulk_create(bulk)
        del bulk

        deelkamp_bk.heeft_deelnemerslijst = True
        deelkamp_bk.save(update_fields=['heeft_deelnemerslijst'])

        # bepaal nu voor elke klasse de volgorde van de deelnemers
        # en zit iedereen boven de cut op deelname=ja
        kamp_mutaties = VerwerkCompKampMutaties(self.stdout, self.my_logger)
        kamp_mutaties.verwerk_mutatie_initieel_deelkamp(deelkamp_bk, zet_boven_cut_op_ja=True)

        # TODO: verstuur uitnodigingen per e-mail

        # behoud maximaal 48 sporters in elke klasse: 24 deelnemers en 24 reserves
        qset = KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk, volgorde__gt=48)
        qset.delete()

    def maak_deelnemerslijst_bk_teams(self, comp):
        # deelfactor om van RK uitslag (60 of 50 pijlen) naar gemiddelde te gaan
        if comp.is_indoor():
            aantal_pijlen = 2.0 * 30
        else:
            aantal_pijlen = 2.0 * 25

        # zoek het BK erbij
        deelkamp_bk = (Kampioenschap
                       .objects
                       .select_related('competitie')
                       .get(deel=DEEL_BK,
                            competitie=comp))

        # verwijder de al aangemaakte teams
        qset = KampioenschapTeam.objects.filter(kampioenschap=deelkamp_bk).all()
        aantal = qset.count()
        if aantal > 0:
            self.stdout.write('[INFO] Alle %s bestaande BK teams worden verwijderd' % aantal)
            qset.delete()

        bulk = list()

        for klasse in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .order_by('volgorde')):

            self.stdout.write('[INFO] Team klasse: %s' % klasse)

            # volgens het reglement doorzetten: de nummers 1 en 2 vanuit elk rayon, indien beschikbaar

            # haal alle teams uit de RK op
            sterkte = list()
            for rk_team in (KampioenschapTeam
                            .objects
                            .filter(kampioenschap__deel=DEEL_RK,
                                    kampioenschap__competitie=comp,
                                    team_klasse_volgende_ronde=klasse,
                                    result_rank__in=(1, 2, 100))         # assumption: nooit meer dan 2 per rayon
                            .select_related('vereniging',
                                            'team_type',
                                            'kampioenschap__rayon')
                            .prefetch_related('gekoppelde_leden')
                            .order_by('result_rank')):

                ag = rk_team.result_teamscore / aantal_pijlen

                bk_team = KampioenschapTeam(
                                kampioenschap=deelkamp_bk,
                                vereniging=rk_team.vereniging,
                                volg_nr=rk_team.volg_nr,
                                team_type=rk_team.team_type,
                                team_naam=rk_team.team_naam,
                                team_klasse=klasse,
                                aanvangsgemiddelde=ag,
                                deelname=DEELNAME_JA)

                bk_team.save()
                self.stdout.write('[INFO] Maak BK team %s.%s (%s)' % (
                                    rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_naam))

                # koppel de RK deelnemers aan het BK team
                pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)
                bk_team.gekoppelde_leden.set(pks)

                tup = (rk_team.result_teamscore, len(sterkte), bk_team)
                sterkte.append(tup)
            # for

            sterkte.sort(reverse=True)      # hoogste eerst
            for rank in range(len(sterkte)):
                tup = sterkte[rank]
                team = tup[-1]
                team.rank = team.volgorde = rank + 1
                team.save(update_fields=['rank', 'volgorde'])
            # for
        # for

# end of file
