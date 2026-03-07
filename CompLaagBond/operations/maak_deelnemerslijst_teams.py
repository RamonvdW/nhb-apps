# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND, KAMP_RANK_BLANCO
from Competitie.models import Competitie, CompetitieMutatie, CompetitieTeamKlasse
from CompKampioenschap.operations import VerwerkCompKampMutaties
from CompKampioenschap.operations import maak_mutatie_update_dirty_wedstrijdformulieren, zet_dirty
from CompLaagBond.models import KampBK, DeelnemerBK, TeamBK
from CompLaagRayon.models import DeelnemerRK, TeamRK


def maak_deelnemerslijst_bk_teams(stdout, comp: Competitie):
    # zoek het BK erbij
    deelkamp_bk = (KampBK
                   .objects
                   .select_related('competitie')
                   .get(competitie=comp))

    # verwijder de al aangemaakte teams
    qset = TeamBK.objects.filter(kamp=deelkamp_bk).all()
    aantal = qset.count()
    if aantal > 0:
        stdout.write('[INFO] Alle %s bestaande BK teams worden verwijderd' % aantal)
        qset.delete()

    for klasse in (CompetitieTeamKlasse
                   .objects
                   .filter(competitie=comp,
                           is_voor_teams_rk_bk=True)
                   .order_by('volgorde')):

        stdout.write('[INFO] Team klasse: %s' % klasse)

        # volgens het reglement doorzetten: de nummers 1 en 2 vanuit elk rayon, indien beschikbaar

        # haal alle teams uit de RK op
        sterkte = list()
        for rk_team in (TeamRK
                        .objects
                        .filter(kamp__competitie=comp,
                                team_klasse_volgende_ronde=klasse,
                                result_rank__in=(1, 2, 100))            # 2 per rayon
                        .select_related('vereniging',
                                        'team_type',
                                        'kamp__rayon')
                        .prefetch_related('gekoppelde_leden')
                        .order_by('result_rank')):

            bk_team = TeamBK.objects.create(
                            kamp=deelkamp_bk,
                            vereniging=rk_team.vereniging,
                            volg_nr=rk_team.volg_nr,
                            team_type=rk_team.team_type,
                            team_naam=rk_team.team_naam,
                            team_klasse=klasse,
                            rk_score=rk_team.result_teamscore,
                            deelname=DEELNAME_JA)

            stdout.write('[INFO] Maak BK team %s.%s (%s)' % (
                            rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_naam))

            # koppel de RK deelnemers aan het BK team
            pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)
            bk_team.gekoppelde_leden.set(pks)

            tup = (rk_team.result_teamscore, len(sterkte), bk_team)
            sterkte.append(tup)
        # for

        rank = 0
        sterkte.sort(reverse=True)      # hoogste eerst
        for tup in sterkte:
            rank += 1
            team = tup[-1]
            team.rank = team.volgorde = rank
            team.save(update_fields=['rank', 'volgorde'])
        # for

        # voeg de reserve teams toe: 2 per rayon
        # haal alle teams uit de RK op
        sterkte = list()
        for rk_team in (TeamRK
                        .objects
                        .filter(kamp__competitie=comp,
                                team_klasse_volgende_ronde=klasse,
                                result_rank__in=(3, 4))            # 2 per rayon
                        .select_related('vereniging',
                                        'team_type',
                                        'kamp__rayon')
                        .prefetch_related('gekoppelde_leden')
                        .order_by('result_rank')):

            bk_team = TeamBK.objects.create(
                            kamp=deelkamp_bk,
                            vereniging=rk_team.vereniging,
                            volg_nr=rk_team.volg_nr,
                            team_type=rk_team.team_type,
                            team_naam=rk_team.team_naam,
                            team_klasse=klasse,
                            rk_score=rk_team.result_teamscore,
                            is_reserve=True,
                            deelname=DEELNAME_ONBEKEND)

            stdout.write('[INFO] Maak reserve BK team %s.%s (%s)' % (
                                rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_naam))

            # koppel de RK deelnemers aan het BK team
            pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)
            bk_team.gekoppelde_leden.set(pks)

            rayon_nr = rk_team.kamp.rayon.rayon_nr

            tup = (0-rayon_nr, rk_team.result_teamscore, len(sterkte), bk_team)
            sterkte.append(tup)
        # for

        sterkte.sort(reverse=True)      # hoogste eerst
        for tup in sterkte:
            rank += 1
            team = tup[-1]
            team.rank = team.volgorde = rank
            team.save(update_fields=['rank', 'volgorde'])
        # for

    # for


# end of file
