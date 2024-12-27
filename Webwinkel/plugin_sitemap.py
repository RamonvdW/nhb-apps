# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Webwinkel.models import WebwinkelProduct
from SiteMap.definities import CHECK_LOW, CHECK_MED   # CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # landing page
    yield CHECK_MED, reverse('Webwinkel:overzicht')

    # product pagina's
    prev_titel = None
    producten = list()
    for product in (WebwinkelProduct
                    .objects
                    .exclude(mag_tonen=False)
                    .order_by('volgorde')):

        is_extern = product.beschrijving.startswith('http')       # is slechts URL naar externe site
        if not is_extern:
            # kleding in verschillende maten hebben dezelfde omslag titel
            # toon alleen de eerste
            if product.omslag_titel != prev_titel:
                tup = (product.pk, product)
                producten.append(tup)
                prev_titel = product.omslag_titel

    # for

    producten.sort()        # sorteer sitemap urls op pk
    for _, product in producten:
        yield CHECK_LOW, reverse('Webwinkel:product', kwargs={'product_pk': product.pk})
    # for


# end of file
