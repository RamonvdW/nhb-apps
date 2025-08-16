# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD
from Evenement.models import Evenement
from SiteMap.definities import CHECK_LOW, CHECK_MED, CHECK_HIGH
import datetime


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # evenementen blijven 2 jaar in de sitemap staan
    now = timezone.now().date()
    lang_geleden = now - datetime.timedelta(days=2 * 365)

    for evenement in (Evenement
                      .objects
                      .exclude(datum__lt=lang_geleden)
                      .filter(status__in=(EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD))
                      .order_by('pk')):

        url = reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk})

        # bereken hoe ver voor/na het evenement, voor dynamische change frequency
        # reken om in weken, zodat we niet elke dag een verandering in de sitemap hebben
        age = now - evenement.datum       # negative = future
        weeks = int(age.days / 7)
        # print(weeks, evenement.datum, evenement.titel)

        if weeks > 2:
            # meer dan 2 weken geleden
            check = CHECK_LOW
        elif weeks < -4:
            # over meer dan 4 weken
            check = CHECK_MED
        else:
            # periode van 4 weken voor (=inschrijven + info updates) tot 21 weken na
            check = CHECK_HIGH

        yield check, url
    # for


# end of file
