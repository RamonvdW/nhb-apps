# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from Kalender.definities import MAAND2URL
from SiteMap.definities import CHECK_LOW, CHECK_MED, CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # landing page
    yield CHECK_LOW, reverse('Kalender:landing-page')

    # rest van de URL's zijn filters, die nemen we niet op

    # alle wedstrijden, evenementen, etc. worden door andere plugins aangeleverd

    # jaaroverzichten en elk maandoverzicht
    now = timezone.now()
    jaar = now.year
    maand = now.month

    for lp in range(24):
        # jaar/<maand>-<jaar>/
        yield CHECK_MED, reverse('Kalender:jaar-simpel',
                                 kwargs={'maand': MAAND2URL[maand],
                                         'jaar': now.year})

        # maand/<maand>-<jaar>/
        yield CHECK_MED, reverse('Kalender:maand-simpel',
                                 kwargs={'maand': MAAND2URL[maand],
                                         'jaar': now.year})

        maand += 1
        if maand == 13:
            maand = 1
            jaar += 1
    # for

# end of file
