# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_GEANNULEERD
from Bestelling.models import BestellingMandje, Bestelling
from Bestelling.operations.mutaties import (bestel_mutatieverzoek_webwinkel_keuze,
                                            bestel_mutatieverzoek_maak_bestellingen, bestel_mutatieverzoek_annuleer)
from Betaal.models import BetaalInstellingenVereniging
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.betaal_sim import fake_betaling
from Vereniging.models import Vereniging
from Webwinkel.definities import KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze


class TestWebwinkelBestelEnBetaal(E2EHelpers, TestCase):

    """ tests voor de applicatie Webwinkel: van mandje tot betaalde factuur """

    test_after = ('Bestelling.tests.test_bestelling',)

    def setUp(self):
        """ initialisatie van de test case """

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()

        self.account_normaal = self.e2e_create_account('100000', 'normaal@test.com', 'Normaal')

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Nor',
                        achternaam='Maal',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2023-04-05',
                        account=self.account_normaal,
                        bij_vereniging=ver,
                        postadres_1='Doelpak baan 12',
                        postadres_2='Appartement 10',
                        postadres_3='1234XY Boogstad')
        sporter.save()
        self.sporter = sporter

        product1 = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        volgorde=1,
                        onbeperkte_voorraad=True,
                        bestel_begrenzing='',
                        prijs_euro="1.23")
        product1.save()

        keuze = WebwinkelKeuze(
                        wanneer=timezone.now(),
                        status=KEUZE_STATUS_RESERVERING_MANDJE,
                        product=product1,
                        aantal=1)
        keuze.save()
        self.keuze1 = keuze

        product2 = WebwinkelProduct(
                        omslag_titel='Test titel 2',
                        volgorde=2,
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='doos,dozen',
                        bestel_begrenzing='1-20',
                        prijs_euro="42.00")
        product2.save()

        keuze = WebwinkelKeuze(
                        wanneer=timezone.now(),
                        status=KEUZE_STATUS_RESERVERING_MANDJE,
                        product=product2,
                        aantal=2)
        keuze.save()
        self.keuze2 = keuze

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        kvk_nummer='kvk1234',
                        contact_email='webwinkel@khsn.not',
                        telefoonnummer='0123456789',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        self.mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_normaal)

    def test_afrekenen(self):
        self.e2e_login(self.account_normaal)

        # leg twee webwinkel producten in het mandje en zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        self.keuze1.refresh_from_db()
        self.keuze2.refresh_from_db()
        self.assertEqual(self.keuze1.status, KEUZE_STATUS_BESTELD)
        self.assertEqual(self.keuze2.status, KEUZE_STATUS_BESTELD)

        bestelling = Bestelling.objects.first()
        fake_betaling(bestelling, self.instellingen_bond)
        self.verwerk_bestel_mutaties()
        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat de webwinkel bestelling nu op 'betaald' staat
        self.keuze1.refresh_from_db()
        self.keuze2.refresh_from_db()
        self.assertEqual(self.keuze1.status, KEUZE_STATUS_BACKOFFICE)
        self.assertEqual(self.keuze2.status, KEUZE_STATUS_BACKOFFICE)

    def test_annuleer_bestelling(self):
        self.e2e_login(self.account_normaal)

        # leg twee webwinkel producten in het mandje en zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        self.keuze1.refresh_from_db()
        self.keuze2.refresh_from_db()
        self.assertEqual(self.keuze1.status, KEUZE_STATUS_BESTELD)
        self.assertEqual(self.keuze2.status, KEUZE_STATUS_BESTELD)

        bestelling = Bestelling.objects.first()
        bestel_mutatieverzoek_annuleer(bestelling, snel=True)
        self.verwerk_bestel_mutaties()

        # keuze records zijn verwijderd
        self.assertEqual(WebwinkelKeuze.objects.filter(pk__in=(self.keuze1.pk, self.keuze2.pk)).count(), 0)

        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_GEANNULEERD)


# end of file
