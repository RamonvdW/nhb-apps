# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Sporter.models import Speelsterkte


def get_hall_of_fame():
    """ Geef de Speelsterkte queries terug van de sporters met pascodes GM, MS, AS,
        elk gesorteerd op datum (oudste eerst) en lidnummer.
        Sporters die niet meer actief lid zijn van een vereniging worden eruit gefilterd.
    """

    qset = (Speelsterkte
            .objects
            .select_related('sporter',
                            'sporter__bij_vereniging')
            .exclude(sporter__bij_vereniging=None)
            .exclude(sporter__bij_vereniging__ver_nr__in=settings.CRM_IMPORT_GEEN_WEDSTRIJDEN)
            .order_by('datum',               # oudste eerst
                      'sporter__lid_nr'))

    leden_gm = qset.filter(pas_code='GM')
    lid_nrs = list(leden_gm.values_list('sporter__lid_nr', flat=True))

    leden_ms = qset.filter(pas_code='MS').exclude(sporter__lid_nr__in=lid_nrs)

    leden_as = qset.filter(pas_code='AS')

    return leden_gm, leden_ms, leden_as


def tel_hall_of_fame():
    """ Geeft het aantal sporters terug dat GM, MS of AS is """

    leden_gm, leden_ms, leden_as = get_hall_of_fame()

    gm_count = leden_gm.count()
    ms_count = leden_ms.count()
    as_count = leden_as.count()

    return gm_count, ms_count, as_count


def get_mogelijke_spelden(discipline: str, boog: str, score: int | None, ):
    """ Bepaalt de mogelijke spelden aan de hand van ingevoerde informatie

        discipline: WEDSTRIJD_DISCIPLINE_* 'OD', 'IN', '25', 'CL', 'VE', 'RA', '3D'
        boog:       BOOGTYPE_AFKORTING_*   'R', 'C', 'BB', 'LB', 'TR'
        score:      De behaalde score

        returns:    [
                        (
                            "speld_cat",     # SPELD_CATEGORIE_*
                            "discipline",    # OD, VE, etc.
                            "afstand(en)",   # een afstand ("18m") of setje afstanden ("90m, 70m, 50m, 30m")
                        ),
                        ...
                    ]

    """

    print('{get_mogelijke_spelden} discpline=%s, boog=%s, score=%s' % (repr(discipline), repr(boog), score))

    spelden = list()

    # WA target awards
    if discipline in ('OD', 'IN') and boog in ('R', 'C', 'BB'):
        pass

    # WA sterspelden
    if discipline == 'OD' and score >= 1000:
        pass



    return spelden


# end of file
