# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.utils import timezone
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd
from SiteMap.definities import CHECK_LOW, CHECK_MED, CHECK_HIGH
import datetime


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # wedstrijden blijven 2 jaar in de sitemap staan
    now = timezone.now().date()
    lang_geleden = now - datetime.timedelta(days=2 * 365)

    for wedstrijd in (Wedstrijd
                      .objects
                      .exclude(datum_begin__lt=lang_geleden)
                      .filter(toon_op_kalender=True,
                              status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD))
                      .order_by('pk')):

        # voor intern gebruik (scheidsrechter beschikbaarheid RK/BK competitie)?
        # verstop_voor_mwz = models.BooleanField(default=False)

        url = reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk})

        # bereken hoe ver voor/na de wedstrijd, voor dynamische change frequency
        # reken om in weken, zodat we niet elke dag een verandering in de sitemap hebben
        age = now - wedstrijd.datum_begin       # negative = future
        weeks = int(age.days / 7)
        # print(weeks, wedstrijd.datum_begin, wedstrijd.titel)
        if weeks > 4:
            # meer dan 4 weken geleden
            check = CHECK_LOW
        elif weeks < -4:
            # over meer dan 4 weken
            check = CHECK_MED
        else:
            # periode van 4 weken voor (=inschrijven + info updates) tot 4 weken na (=publicatie uitslag)
            check = CHECK_HIGH

        yield check, url
    # for


# end of file
