# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from SiteMap.definities import CHECK_LOW


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    yield CHECK_LOW, reverse('Plein:plein')
    yield CHECK_LOW, reverse('Plein:privacy')

    yield CHECK_LOW, reverse('Account:login')
    yield CHECK_LOW, reverse('Account:wachtwoord-vergeten')

    yield CHECK_LOW, reverse('Registreer:begin')
    yield CHECK_LOW, reverse('Registreer:lid')
    yield CHECK_LOW, reverse('Registreer:gast')


# end of file