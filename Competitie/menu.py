# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.models import Competitie


def get_url_voor_competitie(functie_nu):
    """ Geef de url terug naar de specifieke bondscompetities overzicht pagina voor de BKO/RKO/RCL """

    # bepaal bij welke competitie deze rol hoort
    afstand = functie_nu.comp_type  # 18/25
    comps = (Competitie
             .objects
             .exclude(is_afgesloten=True)
             .filter(afstand=afstand)
             .order_by('begin_jaar'))     # laagste (oudste) eerst

    if len(comps) == 1:         # pragma: no branch
        url = reverse('CompBeheer:overzicht', kwargs={'comp_pk': comps[0].pk})
    else:                       # pragma: no cover
        # er zijn geen competities, of er zijn meerdere competities om uit te kiezen
        url = reverse('Competitie:kies')

    return url

# end of file
