# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from Bestelling.models import BestellingMandje, Bestelling, BestellingMutatie


def _verwijder_oude_bestellingen(stdout, max_age):
    objs = (Bestelling
            .objects
            .filter(aangemaakt__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude bestellingen' % count)
        objs.delete()


def _verwijder_lege_mandjes(stdout, max_age):
    objs = (BestellingMandje
            .objects
            .annotate(num_producten=Count("producten"))
            .filter(num_producten=0))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s lege mandjes' % count)
        objs.delete()


def _verwijder_oude_mutaties(stdout, max_age):
    objs = (BestellingMutatie
            .objects
            .filter(when__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude bestellingen mutaties' % count)
        objs.delete()


def bestel_opschonen(stdout):
    """ Database opschonen:
        - verwijder bestellingen die ouder zijn dan 18 maanden
        - verwijder lege mandjes
        - verwijder adresgegevens van bestellingen gast-accounts

        Let op: verwijderen van regels uit het mandje wordt door de bestel_mutaties achtergrondtaak gedaan
    """

    # na 2 jaar verwijderen
    now = timezone.now()
    max_age = now - timedelta(days=2*365)

    _verwijder_oude_bestellingen(stdout, max_age)
    _verwijder_lege_mandjes(stdout, max_age)
    _verwijder_oude_mutaties(stdout, max_age)


# end of file
