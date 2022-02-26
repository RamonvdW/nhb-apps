# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from .models import Competitie


def get_url_voor_competitie(functie_nu):
    """ Geef de url terug naar de specifieke bondscompetities overzicht pagina voor de BKO/RKO/RCL """

    # bepaal bij welke competitie deze rol hoort
    afstand = functie_nu.comp_type  # 18/25
    comps = Competitie.objects.filter(afstand=afstand).order_by('begin_jaar')  # laagste (oudste) eerst

    if len(comps) > 0:
        url = reverse('Competitie:overzicht', kwargs={'comp_pk': comps[0].pk})
    else:
        # er zijn competities
        url = None

    return url

# end of file
