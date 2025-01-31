# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Account.models import Account
from Functie.models import Functie
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Taken.operations import check_taak_bestaat, maak_taak
import datetime


def emailadres_is_geblokkeerd(email: str):
    """
        Deze functie wordt aangeroepen als een mail niet af te leveren is en resulteert in een foutcode
        die aangeeft dat het e-mailadres het probleem is.
    """

    now = timezone.now()
    now = timezone.localtime(now)
    stamp_str = now.strftime('%Y-%m-%d om %H:%M')

    # maak een taak aan om aandacht te krijgen voor de slechte e-mailadres
    regels = list()
    regels.append('Het zijn problemen met het e-mailadres %s' % email)
    regels.append('')
    regels.append('Het e-mailadres wordt hiervoor gebruikt:')

    # kijk of we kunnen vinden bij wie deze hoort
    for gast in GastRegistratie.objects.filter(email=email):
        regels.append('- Gastregistratie %s' % gast.lid_nr)
    # for

    for sporter in Sporter.objects.filter(email=email):
        regels.append('- Sporter / lid %s' % sporter.lid_nr)
    # for

    for account in Account.objects.filter(bevestigde_email=email):
        regels.append('- Account %s (bevestigde e-mail)' % account.username)
    # for

    for account in Account.objects.filter(nieuwe_email=email):
        regels.append('- Account %s (nieuwe e-mail)' % account.username)
    # for

    for functie in Functie.objects.filter(bevestigde_email=email):
        regels.append('- Functie %s (bevestigde e-mail)' % functie.beschrijving)
    # for

    for functie in Functie.objects.filter(nieuwe_email=email):
        regels.append('- Functie %s (nieuwe e-mail)' % functie.beschrijving)
    # for

    beschrijving = '\n'.join(regels)

    taak_onderwerp = "Probleem met e-mailadres"

    # maak een taak aan met alle details
    taak_log = "[%s] Taak aangemaakt" % stamp_str
    taak_deadline = now + datetime.timedelta(days=7)

    functie = Functie.objects.get(rol='SUP')

    # voorkom dubbele meldingen (ook als deze al afgehandeld is)
    if not check_taak_bestaat(skip_afgerond=False,
                              toegekend_aan_functie=functie,
                              beschrijving=beschrijving):

        maak_taak(toegekend_aan_functie=functie,
                  deadline=taak_deadline,
                  aangemaakt_door=None,  # systeem
                  onderwerp=taak_onderwerp,
                  beschrijving=beschrijving,
                  log=taak_log)


# end of file
