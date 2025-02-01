# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Functie.models import Functie
from Opleiding.models import OpleidingInschrijving
from Taken.operations import check_taak_bestaat, maak_taak
import datetime


def opleiding_post_import_crm(stdout):
    """ Deze functie wordt aangeroepen vanuit ImportCRM, nadat een nieuwe import gedaan is
        Doel van deze functie:
        - Kijk of persoonsgegevens doorgevoerd zijn in CRM
        - Maak 1x per week taak voor MO om persoonsgegevens door te zetten
    """

    verschillen = list()
    for inschrijving in (OpleidingInschrijving
                         .objects
                         .exclude(aanpassing_geboorteplaats='')
                         .select_related('sporter')
                         .order_by('wanneer_aangemeld')):

        if inschrijving.sporter.geboorteplaats != inschrijving.aanpassing_geboorteplaats:
            verschillen.append(inschrijving)
    # for

    count = len(verschillen)
    if count > 0:
        stdout.write('[INFO] Inschrijving voor opleiding met geboorteplaats die afwijkt van CRM: %s' % count)

        functie_mo = Functie.objects.get(rol="MO")

        onderwerp = 'Gegevens overnemen'
        beschrijving = 'Van %s deelnemers aan opleidingen moeten persoonsgegevens overgenomen in het CRM.\n' % count
        beschrijving += '\n'
        beschrijving += 'Wissel naar rol Manager Opleidingen en kies het kaartje "Aanpassingen".\n'

        taak = check_taak_bestaat(skip_afgerond=False,
                                  aangemaakt_door=None,
                                  toegekend_aan_functie=functie_mo,
                                  onderwerp=onderwerp)

        if taak:
            # taak is de meest recente
            if taak.deadline > timezone.now().date():
                # deadline is nog niet verlopen
                return

        # deadline is verlopen, of nog geen taak aanwezig
        deadline = timezone.now() + datetime.timedelta(days=7)
        deadline = deadline.date()
        stdout.write('[INFO] Maak taak voor Manager Opleidingen met deadline %s' % deadline)
        maak_taak(aangemaakt_door=None,
                  toegekend_aan_functie=functie_mo,
                  deadline=deadline,
                  onderwerp=onderwerp,
                  beschrijving=beschrijving)


# end of file
