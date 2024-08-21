# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Commando om een evenement aan te maken voor tijdens ontwikkeling
"""

from django.core.management.base import BaseCommand
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement
from Locatie.models import EvenementLocatie
from Vereniging.models import Vereniging


class Command(BaseCommand):

    help = "Maak een test evenement aan"

    def handle(self, *args, **options):

        ver = Vereniging.objects.get(ver_nr=1368)

        self.stdout.write('[INFO] Maak evenement locatie')
        locatie = EvenementLocatie(
                    naam='Arnhemhal',
                    vereniging=ver,
                    adres='Papendallaan 9\n6816VD Arnhem',
                    plaats='Arnhem')
        locatie.save()

        self.stdout.write('[INFO] Maak evenement')
        evenement = Evenement(
                        titel='Dag van de Handboogsport',
                        status=EVENEMENT_STATUS_GEACCEPTEERD,
                        organiserende_vereniging=ver,
                        datum='2024-10-12',
                        aanvang='09:30',
                        inschrijven_tot=1,
                        locatie=locatie,
                        beschrijving='Een dag voor workshops en clinics voor iedereen uit de handboogsport, van schutter tot bestuurder.',
                        # prijs_euro_normaal="15",
                        # prijs_euro_onder18="15",
                        contact_naam='Dhr. Organisator',
                        contact_email='info@handboogsport.nl',
                        contact_website='www.handboogsport.nl',
                        contact_telefoon='023-1234567')
        evenement.save()


# end of file
