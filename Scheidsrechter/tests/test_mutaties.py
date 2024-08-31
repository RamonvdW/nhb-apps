# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_VERENIGING
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Scheidsrechter.definities import SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN
from Scheidsrechter.models import ScheidsMutatie
from Scheidsrechter.mutaties import scheids_mutaties_ping
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import WedstrijdSessie, Wedstrijd
import datetime
import time


class TestScheidsrechterBeschikbaarheid(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; mutaties + achtergrondtaak """

    test_after = ('Account', 'Sporter', 'Wedstrijden', 'Locatie', 'Vereniging', 'Functie')

    testdata = None
    sr3_met_account = None
    sr4_met_account = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:                             # pragma: no branch
                cls.sr4_met_account = sporter
                sporter.adres_lat = 'sr4_lat'
                sporter.adres_lon = 'sr4_lon'
                sporter.save(update_fields=['adres_lat', 'adres_lon'])
                break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_VERENIGING]:       # pragma: no branch
            if sporter.account is not None:                             # pragma: no branch
                cls.sr3_met_account = sporter
                sporter.adres_lat = 'sr3_lat'
                sporter.adres_lon = 'sr3_lon'
                sporter.save(update_fields=['adres_lat', 'adres_lon'])
                break
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.sr3_met_account)
        self.assertIsNotNone(self.sr4_met_account)
        self.functie_cs = Functie.objects.get(rol='CS')

        # maak een wedstrijd aan waar scheidsrechters op nodig zijn
        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=116))
        ver.save()
        self.ver1 = ver

        now = timezone.now()
        datum = now.date()      # pas op met testen ronde 23:59

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres="Schietweg 1, Spanningen",
                        plaats="Spanningen",
                        adres_lat='loc_lat',
                        adres_lon='loc_lon')
        locatie.save()
        locatie.verenigingen.add(ver)
        self.locatie = locatie

        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum + datetime.timedelta(days=1),
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00,
                        aantal_scheids=2)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()

        klasse = KalenderWedstrijdklasse.objects.first()
        sessie.wedstrijdklassen.add(klasse)

        self.wedstrijd = wedstrijd

        # nog een wedstrijd op dezelfde datum, bij een andere vereniging
        # maak een wedstrijd aan waar scheidsrechters op nodig zijn
        ver2 = Vereniging(
                    ver_nr=1001,
                    naam="Andere Club",
                    regio=Regio.objects.get(regio_nr=110))
        ver2.save()

        wedstrijd2 = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver2,
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00,
                        aantal_scheids=1)
        wedstrijd2.save()
        self.wedstrijd2 = wedstrijd2

    def test_empty(self):
        # corner case: ping de achtergrondtaak zonder dat er een mutatie is
        scheids_mutaties_ping.ping()

        # corner case: pad door de code waar 5 seconden gewacht wordt
        self.verwerk_scheids_mutaties(2)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        mutatie = ScheidsMutatie()
        self.assertTrue(str(mutatie) != '')

        mutatie.is_verwerkt = True
        mutatie.mutatie = SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN
        self.assertTrue(str(mutatie) != '')

    def test_mainloop(self):
        ScheidsMutatie(
                mutatie=42,
                door='test 1',
                wedstrijd=self.wedstrijd).save()

        f1, f2 = self.verwerk_scheids_mutaties(2)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[ERROR] Onbekende mutatie code 42" in f2.getvalue())

    def test_stop_exactly(self):
        now = datetime.datetime.now()
        if now.minute == 0:                             # pragma: no cover
            print('Waiting until clock is past xx:00')
            while now.minute == 0:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        now = datetime.datetime.now()
        if now.second > 55:                             # pragma: no cover
            print('Waiting until clock is past xx:xx:59')
            while now.second > 55:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the current minute
        f1, f2 = self.run_management_command('scheids_mutaties', '1', '--quick', '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        f1, f2 = self.run_management_command('scheids_mutaties', '1', '--quick', '--stop_exactly=%s' % (now.minute - 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        now = datetime.datetime.now()
        if now.minute == 59:                             # pragma: no cover
            print('Waiting until clock is past xx:59')
            while now.minute == 59:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the positive case
        f1, f2 = self.run_management_command('scheids_mutaties', '1', '--quick', '--stop_exactly=%s' % (now.minute + 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))


# end of file
