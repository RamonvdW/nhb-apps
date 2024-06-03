# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from Bestel.models import BestelMandje, Bestelling


def bestel_opschonen(stdout):
    """ Database opschonen:
        - verwijder bestellingen die ouder zijn dan 18 maanden
        - verwijder lege mandjes
        - verwijder adresgegevens van bestellingen gast-accounts
    """

    if True:
        # na 24 maanden verwijderen
        now = timezone.now()
        max_age = now - timedelta(days=365 + 365)

        objs = (Bestelling
                .objects
                .filter(aangemaakt__lt=max_age))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s oude bestellingen' % count)
            objs.delete()

    if True:
        objs = (BestelMandje
                .objects
                .annotate(num_producten=Count("producten"))
                .filter(num_producten=0))

        count = objs.count()
        if count > 0:
            stdout.write('[INFO] Verwijder %s lege mandjes' % count)
            objs.delete()

# end of file
