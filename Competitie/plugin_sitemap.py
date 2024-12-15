# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Competitie.models import Competitie
from SiteMap.definities import CHECK_LOW, CHECK_MED  # CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    yield CHECK_LOW, reverse('Competitie:info-competitie')
    yield CHECK_LOW, reverse('Competitie:info-teamcompetitie')
    yield CHECK_LOW, reverse('HistComp:top')
    yield CHECK_LOW, reverse('Competitie:kies')
    yield CHECK_LOW, reverse('Sporter:leeftijdsgroepen')

    for comp in Competitie.objects.order_by('pk'):
        if comp.is_openbaar_voor_publiek():
            yield CHECK_MED, reverse('Competitie:overzicht',
                                     kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})

            yield CHECK_MED, reverse('Competitie:klassengrenzen-tonen',
                                     kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()})
    # for

# end of file
