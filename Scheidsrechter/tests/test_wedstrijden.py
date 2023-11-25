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
from Locatie.models import Locatie, Reistijd
from Scheidsrechter.definities import BESCHIKBAAR_JA, BESCHIKBAAR_NEE, BESCHIKBAAR_DENK
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, ORGANISATIE_IFAA
from Wedstrijden.models import WedstrijdSessie, Wedstrijd
from datetime import timedelta


class TestScheidsrechterWedstrijden(E2EHelpers, TestCase):

    """ tests voor de Scheidsrechter applicatie; module Overzicht """

    test_after = ('Account',)

    url_overzicht = '/scheidsrechter/'
    url_wedstrijden = '/scheidsrechter/wedstrijden/'
    url_wedstrijd_details = '/scheidsrechter/wedstrijden/details/%s/'     # wedstrijd_pk
    url_beschikbaarheid_opvragen = '/scheidsrechter/beschikbaarheid-opvragen/'

    testdata = None

    sr3_met_account = None

    lijst_hsr = list()
    lijst_sr = list()

    hsr_beschikbaar_pk = 0
    hsr_scheids_pk = 0
    hsr_niet_beschikbaar_pk = 0
    sr_niet_beschikbaar_pk = 0

    lijst_sr_beschikbaar_pk = list()
    lijst_sr_scheids_pk = list()

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.sr3_met_account = sporter
                sporter.adres_lat = 'sr3_lat'
                sporter.adres_lon = 'sr3_lon'
                sporter.save(update_fields=['adres_lat', 'adres_lon'])
                break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_BOND]:             # pragma: no branch
            if sporter.account is not None:
                cls.lijst_hsr.append(sporter)
                if len(cls.lijst_hsr) == 5:
                    break
        # for

        for sporter in data.sporters_scheids[SCHEIDS_VERENIGING]:       # pragma: no branch
            if sporter.account is not None:
                cls.lijst_sr.append(sporter)
                if len(cls.lijst_sr) == 10:
                    break
        # for

    def setUp(self):
        """ initialisatie van de test case """
        self.assertIsNotNone(self.sr3_met_account)
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
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdrop',
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
                        datum_einde=datum, # + timedelta(days=1),
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

    def test_anon(self):
        resp = self.client.get(self.url_wedstrijden)
        self.assert_is_redirect_login(resp, self.url_wedstrijden)

        url = self.url_wedstrijd_details % self.wedstrijd.pk
        resp = self.client.get(url)
        self.assert_is_redirect_login(resp, url)

    def test_sr3(self):
        self.e2e_login(self.sr3_met_account.account)

        # zet de reistijd
        Reistijd(vanaf_lat='sr3_lat',
                 vanaf_lon='sr3_lon',
                 naar_lat=self.locatie.adres_lat,
                 naar_lon=self.locatie.adres_lon,
                 reistijd_min=42).save()

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # wedstrijd details
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # corner case
        resp = self.client.post(url)
        self.assert403(resp, 'Mag niet wijzigen')

        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijden)
        self.e2e_assert_other_http_commands_not_supported(self.url_wedstrijd_details % 999999, post=False)

    def test_cs_opvragen(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # wedstrijden
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_wedstrijden)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijden.dtl', 'plein/site_layout.dtl'))

        # wedstrijd details
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # beschikbaarheid opvragen
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.verwerk_scheids_mutaties()
        self.assertEqual(1, WedstrijdDagScheidsrechters.objects.count())

        # wedstrijd details (beschikbaarheid opgevraagd)
        url = self.url_wedstrijd_details % self.wedstrijd.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # wijzig het aantal benodigde scheidsrechters
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 5})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(5, wedstrijd.aantal_scheids)

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 99})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(5, wedstrijd.aantal_scheids)       # no change

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': 'X'})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        wedstrijd = Wedstrijd.objects.get(pk=self.wedstrijd.pk)
        self.assertEqual(1, wedstrijd.aantal_scheids)       # default

        resp = self.client.get(self.url_wedstrijd_details % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.post(self.url_wedstrijd_details % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        self.wedstrijd.locatie.adres_uit_crm = True
        self.wedstrijd.locatie.save(update_fields=['adres_uit_crm'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        self.wedstrijd.locatie.plaats = '(diverse)'
        self.wedstrijd.locatie.save(update_fields=['plaats'])
        self.wedstrijd.organisatie = ORGANISATIE_IFAA
        self.wedstrijd.save(update_fields=['organisatie'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

    def _zet_beschikbaarheid(self, wedstrijd, dag_offset):
        datum = wedstrijd.datum_begin + timedelta(days=dag_offset)
        keuzes = [BESCHIKBAAR_JA, BESCHIKBAAR_NEE, BESCHIKBAAR_DENK]
        keuze_nr = 0

        for sr in self.lijst_hsr:
            opgaaf = keuzes[keuze_nr]
            keuze_nr = (keuze_nr + 1) % len(keuzes)

            beschikbaar = ScheidsBeschikbaarheid(
                                    scheids=sr,
                                    wedstrijd=wedstrijd,
                                    datum=datum,
                                    opgaaf=opgaaf)
            beschikbaar.save()

            if opgaaf == BESCHIKBAAR_JA:
                self.hsr_beschikbaar_pk = beschikbaar.pk
                self.hsr_scheids_pk = sr.pk

            if opgaaf == BESCHIKBAAR_NEE:
                self.hsr_niet_beschikbaar_pk = beschikbaar.pk
        # for

        for sr in self.lijst_sr:
            opgaaf = keuzes[keuze_nr]
            keuze_nr = (keuze_nr + 1) % len(keuzes)

            beschikbaar = ScheidsBeschikbaarheid(
                                    scheids=sr,
                                    wedstrijd=wedstrijd,
                                    datum=datum,
                                    opgaaf=opgaaf)
            beschikbaar.save()

            if opgaaf == BESCHIKBAAR_JA:
                self.lijst_sr_beschikbaar_pk.append(beschikbaar.pk)
                self.lijst_sr_scheids_pk.append(sr.pk)
            if opgaaf == BESCHIKBAAR_NEE:
                self.sr_niet_beschikbaar_pk = beschikbaar.pk
        # for

    def test_cs_kies_sr(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_cs)
        self.e2e_check_rol('CS')

        # beschikbaarheid opvragen
        self.assertEqual(0, WedstrijdDagScheidsrechters.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_beschikbaarheid_opvragen, {'wedstrijd': self.wedstrijd.pk, 'snel': 1})
        self.assert_is_redirect(resp, self.url_overzicht)
        self.verwerk_scheids_mutaties()
        self.assertEqual(1, WedstrijdDagScheidsrechters.objects.count())
        dag = WedstrijdDagScheidsrechters.objects.first()

        # geeft SR beschikbaarheid in
        self._zet_beschikbaarheid(self.wedstrijd, 0)

        url = self.url_wedstrijd_details % self.wedstrijd.pk

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # maak keuzes
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  self.hsr_beschikbaar_pk,
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[0]: 'ja',
                                          'sr_0_%s' % self.lijst_sr_beschikbaar_pk[1]: 'ja',
                                          'sr_0_%s' % self.hsr_beschikbaar_pk: 'ja'})        # dubbele keuze: hsr + sr
        self.assert_is_redirect(resp, self.url_wedstrijden)
        dag = WedstrijdDagScheidsrechters.objects.get(pk=dag.pk)
        self.assertEqual(dag.gekozen_hoofd_sr.pk, self.hsr_scheids_pk)
        self.assertEqual(dag.gekozen_sr1.pk, self.lijst_sr_scheids_pk[0])
        self.assertEqual(dag.gekozen_sr2.pk, self.lijst_sr_scheids_pk[1])
        self.assertIsNone(dag.gekozen_sr3)

        # niet meer beschikbaar maken
        beschikbaar = ScheidsBeschikbaarheid(pk=self.hsr_beschikbaar_pk)
        beschikbaar.opgaaf = BESCHIKBAAR_NEE
        beschikbaar.save(update_fields=['opgaaf'])

        beschikbaar = ScheidsBeschikbaarheid(pk=self.lijst_sr_beschikbaar_pk[1])
        beschikbaar.opgaaf = BESCHIKBAAR_NEE
        beschikbaar.save(update_fields=['opgaaf'])

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # keuze uitzetten
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0':  'geen'})
        self.assert_is_redirect(resp, self.url_wedstrijden)
        dag = WedstrijdDagScheidsrechters.objects.get(pk=dag.pk)
        self.assertIsNone(dag.gekozen_hoofd_sr)
        self.assertIsNone(dag.gekozen_sr1)
        self.assertIsNone(dag.gekozen_sr2)

        # wedstrijd details
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('scheidsrechter/wedstrijd-details.dtl', 'plein/site_layout.dtl'))

        # corner cases
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'aantal_scheids': self.wedstrijd.aantal_scheids,
                                          'hsr_0': 999999})
        self.assert404(resp, 'Slechte parameter (1)')


# end of file
