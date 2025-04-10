# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, Kwalificatiescore


def _verwijder_oude_inschrijvingen(stdout, max_age):
    qset = (WedstrijdInschrijving
            .objects
            .filter(wanneer__lt=max_age))

    count = qset.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude bestellingen' % count)
        # kwalificatiescores gaan automatisch mee
        qset.delete()


def _verwijder_oude_wedstrijden(stdout, max_age):
    qset = (Wedstrijd
            .objects
            .filter(datum_begin__lt=max_age))
    count = qset.count()

    if count > 0:
        sessie_pks = list()
        for wedstrijd in qset:
            pks = list(wedstrijd.sessies.values_list('pk', flat=True))
            sessie_pks.extend(pks)
        # for

        qset2 = WedstrijdSessie.objects.filter(pk__in=sessie_pks)
        count2 = qset2.count()

        stdout.write('[INFO] Verwijder %s oude wedstrijden met %s wedstrijd sessies' % (count, count2))
        qset2.delete()
        qset.delete()


def _verwijder_orphan_sessies(stdout):
    qset = (WedstrijdSessie
            .objects
            .annotate(num_wedstrijden=Count("wedstrijd"))
            .filter(num_wedstrijden=0))

    count = qset.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s orphan wedstrijd sessies' % count)
        qset.delete()


def wedstrijden_opschonen(stdout):
    """ Database opschonen:
        - wedstrijdinschrijvingen die ouder zijn dan 24 maanden
        - wedstrijden die ouder zijn dan 24 maanden
        - kortingen die ouder zijn dan 24 maanden
        - kwalificatiescores die ouder zijn dan 18 maanden
    """

    # na 2 jaar verwijderen
    now = timezone.now()
    max_age = now - timedelta(days=2*365)

    _verwijder_oude_inschrijvingen(stdout, max_age)
    _verwijder_oude_wedstrijden(stdout, max_age)
    _verwijder_orphan_sessies(stdout)


# end of file
