# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

"""
    Management commando dat 1x per week gedraaid wordt (crontab) om een e-mail te sturen als herinnering
    aan bestellingen voor een wedstrijd/evenement bij de vereniging die als status wacht-op-betaling hebben
    en misschien via een bankoverschrijving betaald zijn. Deze moeten handmatig ingevoerd worden.
"""

from django.utils import timezone
from django.core.management.base import BaseCommand
from Bestelling.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_EVENEMENT,
                                   BESTELLING_REGEL_CODE_OPLEIDING)
from Bestelling.models import Bestelling
from Functie.models import Functie
from Taken.operations import check_taak_bestaat, maak_taak
from Vereniging.models import Vereniging
import datetime


class Command(BaseCommand):

    help = "Stuur herinnering bankoverschrijving invoeren"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        now = timezone.now()
        self._stamp_str = now.strftime('%Y-%m-%d om %H:%M')

        self._kort_geleden = now - datetime.timedelta(days=2)
        self._lang_geleden = now - datetime.timedelta(days=90)
        self._taak_deadline = now + datetime.timedelta(days=7)

        self._functie_hwl = dict()      # [ver_nr] = Functie
        for functie in Functie.objects.filter(rol='HWL').select_related('vereniging'):
            self._functie_hwl[functie.vereniging.ver_nr] = functie
        # for

    def _maak_taak(self, ver: Vereniging, aantal: int, producten: str):
        regels = list()

        regels.append('Dit is een wekelijkse herinnering ' +
                      'om handmatige bankoverschrijvingen in te voeren in MijnHandboogsport.')
        regels.append('')
        regels.append('Er zijn %s onbetaalde bestellingen voor %s bij jullie vereniging.' % (aantal, producten))
        regels.append('')
        regels.append('Controleer jullie bankrekening voor handmatige overschrijvingen van sporters. ' +
                      'Deze moeten door de HWL ingevoerd worden via het kaartje "Overboekingen".')
        regels.append('')
        regels.append('Dat maakt de bestelling (en inschrijving) definitief in de lijst van inschrijvingen.')
        regels.append('De sporter ziet dat zijn betaling aangekomen is en dat voorkomt vragen.')

        beschrijving = '\n'.join(regels)

        taak_onderwerp = "Overboekingen invoeren"

        # maak een taak aan met alle details
        taak_log = "[%s] Taak aangemaakt" % self._stamp_str

        functie = self._functie_hwl[ver.ver_nr]

        # voorkom dubbele meldingen (ook als deze al afgehandeld is)
        if not check_taak_bestaat(toegekend_aan_functie=functie,
                                  beschrijving=beschrijving):

            maak_taak(toegekend_aan_functie=functie,
                      deadline=self._taak_deadline,
                      aangemaakt_door=None,  # systeem
                      onderwerp=taak_onderwerp,
                      beschrijving=beschrijving,
                      log=taak_log)

    def _get_ver_nrs(self):
        qset = (Bestelling
                .objects
                .filter(aangemaakt__lt=self._kort_geleden,
                        aangemaakt__gt=self._lang_geleden)
                .exclude(status=BESTELLING_STATUS_GEANNULEERD)
                .exclude(status=BESTELLING_STATUS_AFGEROND)
                .order_by('ontvanger__vereniging__ver_nr')
                .distinct('ontvanger__vereniging__ver_nr')
                .values_list('ontvanger__vereniging__ver_nr', flat=True))

        return list(qset)

    def _zoek_verwacht(self, ver_nr):
        """ retourneer een lijst met nog niet betaalde bestellingen van minimaal 2 dagen oud """

        qset = (Bestelling
                .objects
                .filter(ontvanger__vereniging__ver_nr=ver_nr,
                        aangemaakt__lt=self._kort_geleden,
                        aangemaakt__gt=self._lang_geleden)
                .exclude(status=BESTELLING_STATUS_GEANNULEERD)
                .exclude(status=BESTELLING_STATUS_AFGEROND)
                .prefetch_related('regels')
                .select_related('ontvanger__vereniging'))

        aantal = qset.count()
        ver = qset.first().ontvanger.vereniging
        self.stdout.write('[INFO] %2s onbetaalde bestellingen voor vereniging %s' % (aantal, ver))

        # bepaal het soort producten voor deze vereniging
        count_wedstrijd = 0
        count_evenement = 0
        count_webwinkel = 0
        count_opleiding = 0

        for bestelling in qset:
            for regel in bestelling.regels.all():
                if regel.code == BESTELLING_REGEL_CODE_WEDSTRIJD:
                    count_wedstrijd += 1
                elif regel.code == BESTELLING_REGEL_CODE_EVENEMENT:
                    count_evenement += 1
                elif regel.code == BESTELLING_REGEL_CODE_WEBWINKEL:
                    count_webwinkel += 1
                elif regel.code == BESTELLING_REGEL_CODE_OPLEIDING:
                    count_opleiding += 1
            # for
        # for

        soort = [beschrijving
                 for count, beschrijving in (
                     (count_wedstrijd, 'wedstrijden'),
                     (count_evenement, 'evenementen'),
                     (count_webwinkel, 'webwinkel producten'),
                     (count_opleiding, 'opleidingen'))
                 if count > 0]
        producten = ' / '.join(soort)

        return ver, aantal, producten

    def handle(self, *args, **options):
        for ver_nr in self._get_ver_nrs():
            ver, aantal, producten = self._zoek_verwacht(ver_nr)
            self._maak_taak(ver, aantal, producten)
        # for

# end of file
