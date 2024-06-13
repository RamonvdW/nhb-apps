# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
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


# end of file
