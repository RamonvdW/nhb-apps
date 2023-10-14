# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_VERENIGING
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.models import Functie
from Geo.models import Regio
from Locatie.models import Locatie
from Scheidsrechter.definities import BESCHIKBAAR_LEEG
from Scheidsrechter.models import ScheidsBeschikbaarheid, WedstrijdDagScheidsrechters
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, ORGANISATIE_IFAA
from Wedstrijden.models import WedstrijdSessie, Wedstrijd
import datetime


class TestScheidsrechterOverzicht(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_plein = '/plein/'
    url_overzicht = '/scheidsrechter/'
    url_beschikbaarheid_opvragen = '/scheidsrechter/beschikbaarheid-opvragen/'
    url_beschikbaarheid_wijzigen = '/scheidsrechter/beschikbaarheid-wijzigen/'
    url_beschikbaarheid_inzien = '/scheidsrechter/beschikbaarheid-inzien/'

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
                break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_VERENIGING]:       # pragma: no branch
            if sporter.account is not None:                             # pragma: no branch
                cls.sr3_met_account = sporter
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

        locatie = Locatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres="Schietweg 1, Spanningen",
                        plaats="Spanningen")
        locatie.save()
        locatie.verenigingen.add(ver)

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

    def test_anon(self):
        resp = self.client.get(self.url_beschikbaarheid_opvragen)
        self.assert403(resp)

        resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assert403(resp)

        resp = self.client.get(self.url_beschikbaarheid_inzien)
        self.assert403(resp)

    def test_sr3(self):
        self.e2e_login(self.sr3_met_account.account)

        # beschikbaarheid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_beschikbaarheid_wijzigen, post=False)

        # beschikbaarheid opvragen voor een wedstrijd
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(2, WedstrijdDagScheidsrechters.objects.count())

        self.client.logout()
        self.e2e_login(self.sr3_met_account.account)

        # beschikbaarheid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opgeven: Nee
        self.assertEqual(0, ScheidsBeschikbaarheid.objects.count())
        name = 'wedstrijd_%s_dag_%s' % (self.wedstrijd.pk, 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: '3'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(1, ScheidsBeschikbaarheid.objects.count())
        beschikbaar = ScheidsBeschikbaarheid.objects.first()
        self.assertEqual(beschikbaar.opgaaf, 'N')       # 3 = Nee

        self.assertTrue(str(beschikbaar) != '')

        # opgegeven beschikbaarheid inzien
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opgeven: Unsupported
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: 'X'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(1, ScheidsBeschikbaarheid.objects.count())
        beschikbaar = ScheidsBeschikbaarheid.objects.first()
        self.assertEqual(beschikbaar.opgaaf, 'N')       # ongewijzigd

        # forceer een niet theoretisch keuze
        beschikbaar.opgaaf = BESCHIKBAAR_LEEG
        beschikbaar.save(update_fields=['opgaaf'])

        # opgegeven beschikbaarheid inzien
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

    def test_sr4(self):
        # beschikbaarheid opvragen voor een wedstrijd
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(2, WedstrijdDagScheidsrechters.objects.count())

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd2.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(3, WedstrijdDagScheidsrechters.objects.count())

        dag = WedstrijdDagScheidsrechters.objects.first()
        self.assertTrue(str(dag) != '')

        self.e2e_login(self.sr4_met_account.account)

        # beschikbaarheid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opgeven: Misschien
        self.assertEqual(0, ScheidsBeschikbaarheid.objects.count())
        name = 'wedstrijd_%s_dag_%s' % (self.wedstrijd.pk, 0)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: '2'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(1, ScheidsBeschikbaarheid.objects.count())
        beschikbaar = ScheidsBeschikbaarheid.objects.first()
        self.assertEqual(beschikbaar.opgaaf, 'D')       # 1 = Denk = misschien

        # beschikbaarheid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid wijzigen: Ja
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: '1'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(1, ScheidsBeschikbaarheid.objects.count())
        beschikbaar = ScheidsBeschikbaarheid.objects.first()
        self.assertEqual(beschikbaar.opgaaf, 'J')       # 1 = Ja

        # beschikbaarheid
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_wijzigen)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-wijzigen.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid gelijk houden: Ja --> Ja
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: '1'})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(1, ScheidsBeschikbaarheid.objects.count())
        beschikbaar = ScheidsBeschikbaarheid.objects.first()
        self.assertEqual(beschikbaar.opgaaf, 'J')       # 1 = Ja

    def test_cs_opvragen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen voor een wedstrijd
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(2, WedstrijdDagScheidsrechters.objects.count())

        # verhoog het aantal scheidsrechters en stuur nieuwe verzoeken
        self.wedstrijd.aantal_scheids += 1
        self.wedstrijd.save(update_fields=['aantal_scheids'])

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(2, WedstrijdDagScheidsrechters.objects.count())

        # corner cases
        resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': 'x'})
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': 999999})
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # check that only POST is possible
        self.e2e_assert_other_http_commands_not_supported(self.url_beschikbaarheid_opvragen, get=True, post=False)

    def test_cs_inzien(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid inzien voor een wedstrijd (geen wedstrijden)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_inzien)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-inzien.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opvragen voor een wedstrijd
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.assertEqual(2, WedstrijdDagScheidsrechters.objects.count())

        # beschikbaarheid inzien voor een wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_inzien)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-inzien.dtl', 'plein/site_layout.dtl'))

        # SR4 geeft beschikbaarheid door
        self.e2e_login(self.sr4_met_account.account)
        name = 'wedstrijd_%s_dag_%s' % (self.wedstrijd.pk, 0)
        resp = self.client.post(self.url_beschikbaarheid_wijzigen, {name: '1'})
        self.assert_is_redirect(resp, self.url_overzicht)

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid inzien voor een wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_beschikbaarheid_inzien)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/beschikbaarheid-inzien.dtl', 'plein/site_layout.dtl'))

    # TODO: keuze SR maken

# end of file
