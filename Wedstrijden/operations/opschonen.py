# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models import Count
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, WedstrijdAfgemeld, WedstrijdKorting
from datetime import datetime, timedelta


def _verwijder_oude_wedstrijden(stdout, max_age: datetime):
    qset1 = (Wedstrijd
            .objects
            .filter(datum_begin__lt=max_age))
    count1 = qset1.count()

    if count1 > 0:
        # sessies
        sessie_pks = list()
        for wedstrijd in qset1:
            pks = list(wedstrijd.sessies.values_list('pk', flat=True))
            sessie_pks.extend(pks)
        # for
        qset2 = WedstrijdSessie.objects.filter(pk__in=sessie_pks)
        count2 = qset2.count()

        # inschrijvingen
        qset3 = (WedstrijdInschrijving
                 .objects
                 .filter(wedstrijd__in=qset1))
        count3 = qset3.count()

        # afmeldingen
        qset4 = (WedstrijdAfgemeld
                .objects
                .filter(wedstrijd__in=qset1))
        count4 = qset4.count()

        stdout.write('[INFO] Verwijder %s oude wedstrijden met %s sessies, %s inschrijvingen en %s afmeldingen' % (
                            count1, count2, count3, count4))
        qset4.delete()
        qset3.delete()
        qset2.delete()
        qset1.delete()


def _verwijder_kortingen(stdout, max_age: datetime):
    qset = WedstrijdKorting.objects.filter(geldig_tot_en_met__lte=max_age)
    count = qset.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s wedstrijdkortingen' % count)
        qset.delete()


def _verwijder_orphan_sessies(stdout):
    qset = (WedstrijdSessie
            .objects
            .annotate(num_wedstrijden=Count("wedstrijd"))
            .filter(num_wedstrijden=0))

    count = qset.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s ongekoppelde wedstrijdsessies' % count)
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

    _verwijder_oude_wedstrijden(stdout, max_age)

    # kortingen die een jaar of langer geleden verliepen kunnen weg
    now = timezone.now()
    max_age = now - timedelta(days=365)
    _verwijder_kortingen(stdout, max_age)

    _verwijder_orphan_sessies(stdout)


# end of file
