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
    yield CHECK_MED, reverse('Kalender:landing-page')
    yield CHECK_LOW, reverse('Kalender:landing-page-jaar')

    # rest van de URL's zijn filters, die nemen we niet op

    # alle wedstrijden, evenementen, etc. worden door andere plugins aangeleverd

    # jaaroverzichten en elk maandoverzicht
    now = timezone.now()
    jaar = now.year
    maand = now.month

    # toon 24 maanden vooruit
    for lp in range(24):
        # jaar/<jaar>/<maand>/
        yield CHECK_MED, reverse('Kalender:simpel',
                                 kwargs={'jaar_of_maand': 'jaar',
                                         'maand': MAAND2URL[maand],
                                         'jaar': now.year})

        # maand/<jaar>/<maand>/
        yield CHECK_MED, reverse('Kalender:simpel',
                                 kwargs={'jaar_of_maand': 'maand',
                                         'maand': MAAND2URL[maand],
                                         'jaar': now.year})

        maand += 1
        if maand == 13:
            maand = 1
            jaar += 1
    # for

# end of file
