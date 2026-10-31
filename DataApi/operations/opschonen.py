# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from DataApi.models import DataApiLidmaatschap
import datetime


def dataapi_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        we zetten de lidcode op "niet tonen" voor lms die langer dan 2 jaar afgemeld zijn
        we verwijderen lms records met een laatste mutatiedatum van 2 jaar geleden
    """

    now = datetime.datetime.now()
    oudste_afmeld_datum = now - datetime.timedelta(days=settings.DDI_LMS_KEEP_HISTORY_DAYS)     # typisch: 2 jaar
    oudste_mutatie_datum = now - datetime.timedelta(days=settings.DDI_LMS_KEEP_MUTATED_DAYS)    # typisch: 6 maanden

    # 2 jaar na afmelden maken we de lidcode leeg
    # zet de mutatie_datum zodat dit actief doorgegeven wordt
    qset = DataApiLidmaatschap.objects.all()
    qset = qset.exclude(afmeld_datum='')
    qset = qset.filter(afmeld_datum__lt=oudste_afmeld_datum)
    qset = qset.filter(lid_nr_doorgeven=True)
    count = qset.count()
    if count > 0:
        stdout.write('[INFO] Opschonen DataApi: %s lidmaatschappen worden op lid_nr_doorgeven=False gezet' % count)
        qset.update(lid_nr_doorgeven=False, mutatie_datum=now)

    # 2 jaar na afmelden verwijderen we het lms record
    # geef nog 6 maanden om de mutatie door te geven
    qset = DataApiLidmaatschap.objects.all()
    qset = qset.exclude(afmeld_datum='')
    qset = qset.exclude(afmeld_datum__gte=oudste_afmeld_datum)
    qset = qset.exclude(mutatie_datum__gte=oudste_mutatie_datum)
    count = qset.count()
    stdout.write('[INFO] Opschonen DataApi: %s lidmaatschappen worden verwijderd' % count)
    if count > 0:
        qset.delete()

# end of file
