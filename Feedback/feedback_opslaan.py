# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Account.models import Account
from Taken.taken import maak_taak, check_taak_bestaat
from .models import Feedback
import datetime


def store_feedback(gebruiker_str, rol_str, op_pagina, volledige_url, bevinding, feedback):
    """ Deze functie wordt aangeroepen vanuit de view waarin de feedback van de gebruiker
        verzameld is. Deze functie slaat de feedback op in een database tabel.
    """

    # prevent double creation (double/triple-click button)
    obj, is_new = Feedback.objects.get_or_create(
                        site_versie=settings.SITE_VERSIE,
                        gebruiker=gebruiker_str[:50],
                        in_rol=rol_str[:100],
                        op_pagina=op_pagina[:50],
                        volledige_url=volledige_url[:250],
                        feedback=feedback,
                        is_afgehandeld=False,
                        bevinding=bevinding)

    if is_new:
        obj.toegevoegd_op = timezone.now()
        obj.save()

    # maak taken aan om door te geven dat er nieuwe feedback is
    now = timezone.now()
    taak_log = "[%s] Taak aangemaakt" % now
    taak_deadline = now + datetime.timedelta(days=7)
    taak_tekst = "Er is nieuwe feedback om te bekijken"

    for account in (Account
                    .objects
                    .filter(username__in=settings.TAAK_OVER_FEEDBACK_ACCOUNTS)):

        if not check_taak_bestaat(toegekend_aan=account, beschrijving=taak_tekst):
            maak_taak(toegekend_aan=account,
                      deadline=taak_deadline,
                      aangemaakt_door=None,         # systeem
                      beschrijving=taak_tekst,
                      log=taak_log)
    # for


# end of file
