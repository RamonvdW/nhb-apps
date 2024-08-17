# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Commando om een evenement aan te maken voor tijdens ontwikkeling
"""

from django.core.management.base import BaseCommand
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD
from Evenement.models import Evenement, EvenementSessie
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
                        contact_naam='Dhr. Organisator',
                        contact_email='info@handboogsport.nl',
                        contact_website='www.handboogsport.nl',
                        contact_telefoon='023-1234567',
                        beschrijving='Een dag voor workshops en clinics voor iedereen uit de handboogsport, van schutter tot bestuurder.',
                        prijs_euro_normaal="15",
                        prijs_euro_onder18="15")
        evenement.save()

        self.stdout.write('[INFO] Maak sessie 1')
        sessie = EvenementSessie(
                    evenement=evenement,
                    titel='Beginnen bij de basis - trainen volgens het basisschot',
                    presentator='Dhr. Presentator',
                    begin_tijd='11:00',
                    duur_min=60,
                    max_deelnemers=30,
                    beschrijving='Het basisschot levert de basisingrediënten voor het aanleren van een schiettechniek voor een leven lang veilig schieten/sporter. Het vormt de basis voor beginnercursussen, trainersopleidingen en het meerjarenopleidingsplan. Ben jij een trainer die nog niet volgens het basisschot trainingen geeft of die weer wat opgefrist wil worden? Dan is deze workshop iets voor jou.')
        sessie.save()

        self.stdout.write('[INFO] Maak sessie 2')
        sessie = EvenementSessie(
                    evenement=evenement,
                    titel='Ik ben topsporter, ask me anything',
                    presentator='Topsporters A+B',
                    begin_tijd='11:00',
                    duur_min=60,
                    max_deelnemers=50,
                    beschrijving='Dit is je kans om onze TeamNL toppers het hemd van het lijf te vragen! Hoe trainen ze? Wat eten ze? Hoe zorgen ze voor balans tussen focus en presteren? En wat is nu eigenlijk hun favoriete eten?')
        sessie.save()

        self.stdout.write('[INFO] Maak sessie 3')
        sessie = EvenementSessie(
                    evenement=evenement,
                    titel='Schieten met Oranje (recurve/compound)',
                    presentator='Topsporters A+B',
                    begin_tijd='13:00',
                    duur_min=60,
                    max_deelnemers=20,
                    beschrijving='Neem je boog mee en schiet met de Nederlandse toppers!')
        sessie.save()

        self.stdout.write('[INFO] Maak sessie 4')
        sessie = EvenementSessie(
                    evenement=evenement,
                    titel='MijHandboogsport - demo wedstrijdkalender',
                    presentator='Ramon',
                    begin_tijd='13:00',
                    duur_min=60,
                    max_deelnemers=30,
                    beschrijving='Heb jij al een account op MijnHandboogsport? Dit online platform van de KHSN wordt al door veel leden gebruikt en telkens verder ontwikkeld. Leer tijdens deze workshop meer over de nieuwe wedstrijdkalender.')
        sessie.save()

        self.stdout.write('[INFO] Maak sessie 5')
        sessie = EvenementSessie(
                    evenement=evenement,
                    titel='Workshop barebow',
                    presentator='Ramon',
                    begin_tijd='14:00',
                    duur_min=60,
                    max_deelnemers=50,
                    beschrijving='Barebows zijn vaak gelijk aan de Olympische recurve bogen, maar dan zonder de stabalisatoren en het vizier. Deze manier van schieten wint aan populariteit, maar vraagt om een andere richttechniek. Kom je het uitproberen?')
        sessie.save()


# end of file
