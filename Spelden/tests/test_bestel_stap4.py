# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Bestelling.operations import bestel_mutatieverzoek_maak_bestellingen
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Spelden.models import Speld, SpeldAanvraagPrep, SpeldToegekend, SpeldAanvraag, SpeldBestelling
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime


class TestSpeldenBestelStap4(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 4 """

    url_begin = '/spelden/'
    url_bestel_stap4 = '/spelden/bestel/stap4/'

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

        # maak een vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()

        # maak de sporter aan
        self.account_sporter = self.e2e_create_account('100001', 'normaal@test.com', 'Normaal')
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver,
                    account=self.account_sporter,
                    email=self.account_sporter.email)
        sporter.save()
        self.sporter_100001 = sporter

        # zet een wedstrijd op de kalender, 2 maanden terug
        now = timezone.now()
        wed_datum = (now - datetime.timedelta(days=60)).date()

        self.locatie = WedstrijdLocatie.objects.create(
                                naam='test',
                                adres='',
                                notities='')

        self.wedstrijd = Wedstrijd.objects.create(
                                status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                datum_begin=wed_datum,
                                datum_einde=wed_datum,
                                organiserende_vereniging=ver,
                                locatie=self.locatie)

        # geef deze sporter al een ster speld (voor de 1440)
        ster_r1000 = Speld.objects.get(volgorde=1001)
        self.toegekend = SpeldToegekend.objects.create(
                            speld=ster_r1000,
                            sporter=self.sporter_100001,
                            datum='2000-01-01')

        # geef deze sporter de laagste graadspeld indoor
        graadspeld_3e = Speld.objects.get(volgorde=5003)
        self.toegekend = SpeldToegekend.objects.create(
                            speld=graadspeld_3e,
                            sporter=self.sporter_100001,
                            datum='2000-01-01')

        # geef deze sporter de laagste graadspeld veld
        graadspeld_3e = Speld.objects.get(volgorde=5201)
        self.toegekend = SpeldToegekend.objects.create(
                            speld=graadspeld_3e,
                            sporter=self.sporter_100001,
                            datum='2000-01-01')

        # geef deze sporter de laagste graadspeld short metric
        graadspeld_3e = Speld.objects.get(volgorde=5301)
        self.toegekend = SpeldToegekend.objects.create(
                            speld=graadspeld_3e,
                            sporter=self.sporter_100001,
                            datum='2000-01-01')

        # geef deze sporter de hoogste meesterspeld
        meesterspeld_allround = Speld.objects.get(volgorde=5403)
        self.toegekend = SpeldToegekend.objects.create(
                            speld=meesterspeld_allround,
                            sporter=self.sporter_100001,
                            datum='2000-01-01')

    def test_stap4_foutjes(self):
        self.e2e_login(self.account_sporter)

        with override_settings(TOON_SPELDEN_BESTELLEN=False):
            resp = self.client.get(self.url_bestel_stap4)
        self.assert404(resp, 'Bestellen is niet mogelijk')

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET zonder SpeldenAanvraagPrep
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assert404(resp, 'Onvolledige verzoek (1)')

            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap4)
            self.assert404(resp, 'Onvolledige verzoek (1)')

            # GET zonder data van stap3
            SpeldAanvraagPrep.objects.create(
                            voor_sporter=self.sporter_100001,
                            heeft_data_stap1=True,
                            heeft_data_stap2=True,
                            heeft_data_stap3=False)

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assert404(resp, 'Onvolledige verzoek (2)')

            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap4)
            self.assert404(resp, 'Onvolledige verzoek (2)')

        self.client.logout()
        resp = self.client.get(self.url_bestel_stap4)
        self.assert403(resp, 'Niet ingelogd')

    def test_stap4_outdoor(self):
        self.e2e_login(self.account_sporter)

        prep = SpeldAanvraagPrep.objects.create(
                                voor_sporter=self.sporter_100001,
                                wedstrijd_geslacht='M',
                                discipline='OD',
                                boog='R',
                                score=1234,
                                heeft_data_stap1=True,
                                datum_wedstrijd=self.wedstrijd.datum_begin.strftime('%Y-%m-%d'),
                                informatie_wedstrijd='Boogstad|Schietland',
                                score_sm=620,
                                heeft_data_stap2=True,
                                afstanden='90, 70, 50, 30',
                                aantal_pijlen=4*36,
                                heeft_data_stap3=True)
        self.assertTrue(str(prep) != '')

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap4.dtl', 'design/site_layout.dtl'))

            # POST
            with self.assert_max_queries(61):
                resp = self.client.post(self.url_bestel_stap4, {'snel': '1'})
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_toegevoegd-aan-mandje.dtl', 'design/site_layout.dtl'))

            aanvraag = SpeldAanvraag.objects.filter(voor_sporter=self.sporter_100001).first()
            self.assertIsNotNone(aanvraag)
            self.assertEqual(aanvraag.score, prep.score)
            self.assertTrue(str(aanvraag) != '')

            # laat de mutaties verwerken door de achtergrondtaak
            self.verwerk_bestel_mutaties()

            # GET met de spelden al in het mandje
            prep = SpeldAanvraagPrep.objects.create(
                            voor_sporter=self.sporter_100001,
                            wedstrijd_geslacht='M',
                            discipline='OD',
                            boog='R',
                            score=1234,
                            heeft_data_stap1=True,
                            datum_wedstrijd=self.wedstrijd.datum_begin.strftime('%Y-%m-%d'),
                            informatie_wedstrijd='Boogstad|Schietland',
                            score_sm=0,     # extra coverage
                            heeft_data_stap2=True,
                            afstanden='90, 70, 50, 30',
                            aantal_pijlen=4 * 36,
                            heeft_data_stap3=True)

            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap4.dtl', 'design/site_layout.dtl'))

            # zet het mandje om in een bestelling
            bestel_mutatieverzoek_maak_bestellingen(self.account_sporter, snel=True)
            self.verwerk_bestel_mutaties()

            # GET met de spelden al in bestelling
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap4.dtl', 'design/site_layout.dtl'))

            # zet de score laag zodat er 0 spelden besteld kunnen worden
            prep.score = 1
            prep.score_sm = 1
            prep.save()
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap4)
            self.assert404(resp, 'Slecht verzoek')

        bestelling = SpeldBestelling.objects.first()
        self.assertTrue(str(bestelling) != '')

    def test_stap4_veld(self):
        self.e2e_login(self.account_sporter)

        prep = SpeldAanvraagPrep.objects.create(
                                voor_sporter=self.sporter_100001,
                                wedstrijd_geslacht='M',
                                discipline='VE',
                                boog='R',
                                score='300',
                                heeft_data_stap1=True,
                                datum_wedstrijd=self.wedstrijd.datum_begin.strftime('%Y-%m-%d'),
                                informatie_wedstrijd='Boogstad|Schietland',
                                heeft_data_stap2=True,
                                aantal_doelen=24,
                                heeft_data_stap3=True)

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET, discipline indoor
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap4.dtl', 'design/site_layout.dtl'))

    def test_stap4_indoor(self):
        self.e2e_login(self.account_sporter)

        prep = SpeldAanvraagPrep.objects.create(
                                voor_sporter=self.sporter_100001,
                                wedstrijd_geslacht='V',     # extra coverage
                                discipline='IN',
                                boog='R',
                                score='593',
                                heeft_data_stap1=True,
                                datum_wedstrijd=self.wedstrijd.datum_begin.strftime('%Y-%m-%d'),
                                wedstrijd=self.wedstrijd,
                                informatie_wedstrijd='Boogstad|Schietland',
                                heeft_data_stap2=True,
                                afstanden='18',
                                aantal_pijlen=60,
                                heeft_data_stap3=True)

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET, discipline indoor
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap4)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap4.dtl', 'design/site_layout.dtl'))


# end of file
