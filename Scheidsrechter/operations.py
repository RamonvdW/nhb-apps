# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Scheidsrechter.models import (WedstrijdDagScheidsrechters, MatchScheidsrechters,
                                   ScheidsBeschikbaarheid, ScheidsMutatie)
import datetime


def get_bezette_scheidsrechters(op_datum, ignore_wedstrijd=None, ignore_match=None):
    """ Geef een lijst terug van SR die al bezet zijn op de opgegeven datum """

    datum_begin = op_datum - datetime.timedelta(days=7)
    datum_einde = op_datum + datetime.timedelta(days=7)

    bezette_sr = list()     # lid_nrs

    for dag in (WedstrijdDagScheidsrechters
                .objects
                .exclude(wedstrijd__datum_begin__lt=datum_begin)
                .exclude(wedstrijd__datum_einde__gt=datum_einde)
                .select_related('wedstrijd',
                                'gekozen_hoofd_sr', 'gekozen_sr1', 'gekozen_sr2', 'gekozen_sr3', 'gekozen_sr4',
                                'gekozen_sr5', 'gekozen_sr6', 'gekozen_sr7', 'gekozen_sr8', 'gekozen_sr9')):

        if dag.wedstrijd != ignore_wedstrijd:
            wed_datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            if wed_datum == op_datum:
                for sr in (dag.gekozen_hoofd_sr, dag.gekozen_sr1, dag.gekozen_sr2, dag.gekozen_sr3,  dag.gekozen_sr4,
                           dag.gekozen_sr5, dag.gekozen_sr6, dag.gekozen_sr7, dag.gekozen_sr8, dag.gekozen_sr9):
                    if sr and sr.lid_nr not in bezette_sr:
                        bezette_sr.append(sr.lid_nr)
                # for
    # for

    for match_sr in (MatchScheidsrechters
                     .objects
                     .filter(match__datum_wanneer=op_datum)
                     .select_related('match',
                                     'gekozen_hoofd_sr', 'gekozen_sr1', 'gekozen_sr2')):

        if match_sr.match != ignore_match:
            for sr in (match_sr.gekozen_hoofd_sr, match_sr.gekozen_sr1, match_sr.gekozen_sr2):
                if sr and sr.lid_nr not in bezette_sr:
                    bezette_sr.append(sr.lid_nr)
            # for
    # for

    return bezette_sr


# end of file
