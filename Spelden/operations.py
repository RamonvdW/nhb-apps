# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Sporter.models import Speelsterkte


def tel_hall_of_fame():
    """ Geeft het aantal sporters terug dat GM, MS of AS is """

    qset = (Speelsterkte
            .objects
            .order_by('datum',
                      'sporter__lid_nr')
            .select_related('sporter',
                            'sporter__bij_vereniging'))

    leden = qset.filter(pas_code='GM')
    lid_nrs = list(leden.values_list('sporter__lid_nr', flat=True))
    gm_count = len(lid_nrs)

    ms_count = qset.filter(pas_code='MS').exclude(sporter__lid_nr__in=lid_nrs).count()

    as_count = qset.filter(pas_code='AS').count()

    return gm_count, ms_count, as_count


# end of file
