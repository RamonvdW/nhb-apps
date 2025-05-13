# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.models import RegiocompetitieSporterBoog
from Wedstrijden.definities import KWALIFICATIE_CHECK_AFGEKEURD, KWALIFICATIE_CHECK2STR
from Wedstrijden.models import WedstrijdInschrijving, Kwalificatiescore


def get_kwalificatie_scores(inschrijving: WedstrijdInschrijving):
    """ bepaal de kwalificatie-scores van een inschrijving:
        - de maximaal 3 opgegeven scores
        - de 4 beste resultaten uit de regiocompetitie

        Geeft een lijst met 0 tot 5 Kwalificatiescore records terug.
    """
    unsorted = list()

    # pak de handmatig opgegeven kwalificatiescores erbij
    scores = (Kwalificatiescore
              .objects
              .filter(inschrijving=inschrijving)
              .exclude(resultaat=0)
              .exclude(check_status=KWALIFICATIE_CHECK_AFGEKEURD)
              .order_by('-resultaat'))  # hoogste eerst

    for score in scores:
        score.naam = '?' if score.naam == '' else score.naam
        score.waar = '?' if score.waar == '' else score.waar
        score.check_str = KWALIFICATIE_CHECK2STR[score.check_status]
        tup = (score.resultaat, score.datum, score.pk, score)
        unsorted.append(tup)
    # for

    now = timezone.now().date()

    # zoek de bondscompetitie Indoor scores erbij
    try:
        deelnemer = (RegiocompetitieSporterBoog
                     .objects
                     .get(sporterboog=inschrijving.sporterboog,
                          regiocompetitie__competitie__afstand='18'))
    except RegiocompetitieSporterBoog.DoesNotExist:
        # doet niet mee aan de competitie
        pass
    else:
        scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                  deelnemer.score5, deelnemer.score6, deelnemer.score7]
        scores = [score for score in scores if score > 0]
        scores.sort(reverse=True)    # hoogste eerst
        scores = scores[:4]          # top 4
        scores.extend([0, 0, 0, 0])  # minimaal 4

        # eerste 60 pijlen score uit de bondscompetitie
        score = Kwalificatiescore(
                    inschrijving=inschrijving,
                    datum=now,
                    naam='Bondscompetitie Indoor',
                    waar='',
                    resultaat=scores[0] + scores[1])
        if score.resultaat > 0:
            score.check_str = 'Automatisch'
            tup = (score.resultaat, score.datum, 1000000000 + inschrijving.pk, score)
            unsorted.append(tup)

        # tweede 60 pijlen score uit de bondscompetitie
        score = Kwalificatiescore(
                    inschrijving=inschrijving,
                    datum=now,
                    naam='Bondscompetitie Indoor',
                    waar='',
                    resultaat=scores[2] + scores[3])
        if score.resultaat > 0:
            score.check_str = 'Automatisch'
            tup = (score.resultaat, score.datum, 1000000001 + inschrijving.pk, score)
            unsorted.append(tup)

    # sorteer de samengevoegde lijst van opgegeven wedstrijdresultaten en automatische data van de bondscompetities
    unsorted.sort(reverse=True)     # hoogste resultaat eerst

    return [score for _, _, _, score in unsorted]


# end of file
