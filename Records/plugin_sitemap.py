# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Records.definities import disc2url
from Records.models import IndivRecord
from SiteMap.definities import CHECK_LOW, CHECK_MED   # CHECK_HIGH


def generate_urls():
    """ deze generator geeft URLs terug voor de sitemap """

    # landing page
    yield CHECK_MED, reverse('Records:overzicht')

    # zoek
    yield CHECK_LOW, reverse('Records:zoek')

    # indiv records
    yield CHECK_LOW, reverse('Records:indiv')

    # individuele records KHSN
    for obj in IndivRecord.objects.order_by('discipline', 'volg_nr'):
        url = reverse('Records:specifiek', kwargs={'discipline': obj.discipline, 'nummer': obj.volg_nr})
        yield CHECK_LOW, url
    # for

    # TODO: team records

    # TODO: IFAA records

    # verbeterbare records
    yield CHECK_LOW, reverse('Records:indiv-verbeterbaar')

    # verbeterbare records top-pagina per discipline
    # (alle/alle/alle = makl, lcat, gesl
    for disc in (IndivRecord
                 .objects
                 .distinct('discipline')
                 .order_by('discipline')
                 .values_list('discipline', flat=True)):

        url = reverse('Records:indiv-verbeterbaar-disc', kwargs={'disc': disc2url[disc],
                                                                 'makl': 'alle',
                                                                 'lcat': 'alle',
                                                                 'gesl': 'alle'})
        yield CHECK_MED, url
    # for

    # eervolle vermeldingen zijn verwijzingen naar externe pagina's, dus geen pagina om toe te voegen


# end of file
