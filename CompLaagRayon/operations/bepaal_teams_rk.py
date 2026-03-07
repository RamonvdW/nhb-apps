# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Competitie, RegiocompetitieSporterBoog
from CompLaagRayon.models import DeelnemerRK, TeamRK


def converteer_rk_teams_tijdelijke_leden(stdout, comp: Competitie):
    """ converteer de sporters die gekoppeld zijn aan de RK teams
        de RK teams zijn die tijdens de regiocompetitie al aangemaakt door de verenigingen
        en er zijn regiocompetitie sporters aan gekoppeld welke misschien niet gerechtigd zijn.

        controleer ook meteen de vereniging van de deelnemer
        als laatste wordt de team sterkte opnieuw berekend

        het vaststellen van de wedstrijdklasse voor de RK teams volgt later
    """

    # maak een look-up tabel van RegioCompetitieSporterBoog naar KampioenschapSporterBoog
    sporterboog_pk2regiocompetitiesporterboog = dict()
    for deelnemer in (RegiocompetitieSporterBoog
                      .objects
                      .select_related('bij_vereniging')
                      .filter(regiocompetitie__competitie=comp)):
        sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk] = deelnemer
    # for

    regiocompetitiesporterboog_pk2kampioenschapsporterboog = dict()
    for deelnemer in (DeelnemerRK
                      .objects
                      .select_related('bij_vereniging')
                      .filter(kamp__competitie=comp)):
        try:
            regio_deelnemer = sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk]
        except KeyError:
            stdout.write('[WARNING] Kan regio deelnemer niet vinden voor kampioenschapsporterboog met pk=%s' %
                            deelnemer.pk)
        else:
            regiocompetitiesporterboog_pk2kampioenschapsporterboog[regio_deelnemer.pk] = deelnemer
    # for

    # sporters mogen maar aan 1 team gekoppeld worden
    gekoppelde_deelnemer_pks = list()

    for team in (TeamRK
                 .objects
                 .filter(kamp__competitie=comp)
                 .select_related('vereniging')
                 .prefetch_related('tijdelijke_leden')):

        team_ver_nr = team.vereniging.ver_nr
        deelnemer_pks = list()

        ags = list()

        for pk in team.tijdelijke_leden.values_list('pk', flat=True):
            try:
                deelnemer = regiocompetitiesporterboog_pk2kampioenschapsporterboog[pk]
            except KeyError:
                # regio sporter is niet doorgekomen naar het RK en valt dus af
                pass
            else:
                # controleer de vereniging
                if deelnemer.bij_vereniging.ver_nr == team_ver_nr:
                    # controleer dat de deelnemer nog niet aan een RK team gekoppeld is
                    if deelnemer.pk not in gekoppelde_deelnemer_pks:
                        gekoppelde_deelnemer_pks.append(deelnemer.pk)

                        deelnemer_pks.append(deelnemer.pk)
                        ags.append(deelnemer.gemiddelde)
        # for

        team.gekoppelde_leden.set(deelnemer_pks)

        # bepaal de team sterkte
        ags.sort(reverse=True)
        if len(ags) >= 3:
            team.aanvangsgemiddelde = sum(ags[:3])
        else:
            team.aanvangsgemiddelde = 0.0

        # de klasse wordt later bepaald als de klassengrenzen vastgesteld zijn
        team.team_klasse = None

        team.save(update_fields=['aanvangsgemiddelde', 'team_klasse'])
    # for

    # FUTURE: maak een taak aan voor de HWL's om de RK teams te herzien (eerst functionaliteit voor HWL maken)


# end of file
