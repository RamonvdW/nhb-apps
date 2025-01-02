# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from SiteMap.definities import CHECK_LOW   # CHECK_MED, CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # landing page
    yield CHECK_LOW, reverse('Kalender:landing-page')

    # rest van de URL's zijn filters, die nemen we niet op

    # alle wedstrijden, evenementen, etc. worden door andere plugins aangeleverd


# end of file
