# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from Vereniging.models import Vereniging
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdKorting, WedstrijdInschrijving, WedstrijdAfgemeld
from Wedstrijden.operations.opschonen import wedstrijden_opschonen
from datetime import timedelta


class TestWedstrijdenOpOpschonen(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, operations Opschonen """

    def setUp(self):
        """ initialisatie van de test case """

        account = self.e2e_create_account('100000', '100000@test.not', 'Ad')

        sporter = Sporter.objects.create(
                    lid_nr=100000,
                    voornaam='Ad',
                    achternaam='de Admin',
                    geboorte_datum='1966-06-06',
                    sinds_datum='2020-02-02',
                    account=account)

        boog_c = BoogType.objects.get(afkorting='C')

        sporterboog = SporterBoog.objects.create(
                            sporter=sporter,
                            boogtype=boog_c,
                            voor_wedstrijd=True)

        # maak een test vereniging
        ver = Vereniging.objects.create(
                            ver_nr=1000,
                            naam="Grote Club",
                            regio=Regio.objects.get(regio_nr=112))

        # voeg een locatie toe
        locatie = WedstrijdLocatie.objects.create(
                            baan_type='E',      # externe locatie
                            naam='Test locatie')
        locatie.verenigingen.add(ver)

        now = timezone.now()
        verlopen_datum = now - timedelta(days=2*366)

        wedstrijd = Wedstrijd.objects.create(
                            titel='test wedstrijd 1',
                            datum_begin=verlopen_datum,
                            datum_einde=verlopen_datum,
                            organiserende_vereniging=ver,
                            voorwaarden_a_status_when=now,
                            locatie=locatie)
        wedstrijd.refresh_from_db()

        sessie = WedstrijdSessie.objects.create(
                        datum=verlopen_datum,
                        tijd_begin='10:00',
                        tijd_einde='17:00')
        wedstrijd.sessies.add(sessie)

        # orphan sessie
        WedstrijdSessie.objects.create(
                        datum=verlopen_datum,
                        tijd_begin='10:00',
                        tijd_einde='17:00')

        WedstrijdKorting.objects.create(
                        geldig_tot_en_met=verlopen_datum,
                        uitgegeven_door=ver)

        wkl = KalenderWedstrijdklasse.objects.filter(organisatie=wedstrijd.organisatie,
                                                     buiten_gebruik=False,
                                                     boogtype=boog_c,
                                                     leeftijdsklasse__volgorde__gte=20).first()
        wedstrijd.wedstrijdklassen.add(wkl)

        WedstrijdInschrijving.objects.create(
                    wanneer=now,
                    wedstrijd=wedstrijd,
                    sessie=sessie,
                    sporterboog=sporterboog,
                    wedstrijdklasse=wkl,
                    koper=account)

        WedstrijdAfgemeld.objects.create(
                    wanneer_afgemeld=now,
                    wanneer_inschrijving=now,
                    reserveringsnummer=1,
                    wedstrijd=wedstrijd,
                    sporterboog=sporterboog,
                    wedstrijdklasse=wkl,
                    koper=account)

    def test_opschonen(self):
        stdout = OutputBuffer()
        wedstrijden_opschonen(stdout)
        print(stdout.getvalue())
        self.assertTrue("[INFO] Verwijder 1 oude wedstrijden met 1 sessies, 1 inschrijvingen en 1 afmeldingen" in stdout.getvalue())
        self.assertTrue("[INFO] Verwijder 1 wedstrijdkortingen" in stdout.getvalue())
        self.assertTrue("[INFO] Verwijder 1 ongekoppelde wedstrijdsessies" in stdout.getvalue())

        # tweede run met 0 opschoningen
        stdout = OutputBuffer()
        wedstrijden_opschonen(stdout)
        # print(stdout.getvalue())
        self.assertEqual("", stdout.getvalue())


# end of file
