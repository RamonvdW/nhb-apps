# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from BasisTypen.models import BoogType
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Spelden.models import SpeldAanvraagPrep
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime


class TestSpeldenBestelStap1(E2EHelpers, TestCase):

    """ tests voor de Spelden applicatie, bestelprocess stap 1 """

    url_begin = '/spelden/'
    url_bestel = '/spelden/bestel/'
    url_bestel_stap1 = '/spelden/bestel/stap1/'
    url_bestel_stap2 = '/spelden/bestel/stap2/'
    url_bestel_stap3 = '/spelden/bestel/stap3/'
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

        boog_bb = BoogType.objects.get(afkorting='BB')

        self.sporterboog = SporterBoog.objects.create(sporter=sporter, boogtype=boog_bb, voor_wedstrijd=True)

        self.voorkeuren = SporterVoorkeuren.objects.create(sporter=sporter, wedstrijd_geslacht_gekozen=False)

        # zet een wedstrijd op de kalender, 2 maanden terug
        now = timezone.now()
        datum = (now - datetime.timedelta(days=60)).date()

        loc = WedstrijdLocatie.objects.create(
                        naam='test',
                        adres='',
                        notities='')

        Wedstrijd.objects.create(
                    status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                    datum_begin=datum,
                    datum_einde=datum,
                    organiserende_vereniging=ver,
                    locatie=loc)

        # nog een wedstrijd, meerdere datums
        Wedstrijd.objects.create(
                    status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                    datum_begin=datum - datetime.timedelta(days=2),
                    datum_einde=datum,
                    organiserende_vereniging=ver,
                    locatie=loc)

        datum -= datetime.timedelta(days=1)
        Wedstrijd.objects.create(
                    status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                    datum_begin=datum,
                    datum_einde=datum,
                    organiserende_vereniging=ver,
                    locatie=loc)

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_bestel)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap1)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap2)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap3)
        self.assert403(resp, 'Niet ingelogd')

        resp = self.client.get(self.url_bestel_stap4)
        self.assert403(resp, 'Niet ingelogd')

    def test_bestel(self):
        self.e2e_login(self.account_sporter)

        with override_settings(TOON_SPELDEN_BESTELLEN=False):
            resp = self.client.get(self.url_bestel)
        self.assert404(resp, 'Bestellen is niet mogelijk')

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            resp = self.client.get(self.url_bestel)
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            prep = SpeldAanvraagPrep.objects.create(voor_sporter=self.sporter_100001)

            resp = self.client.get(self.url_bestel)
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            prep.heeft_data_stap1 = True
            prep.save()
            resp = self.client.get(self.url_bestel)
            self.assert_is_redirect(resp, self.url_bestel_stap2)

            prep.heeft_data_stap2 = True
            prep.save()
            resp = self.client.get(self.url_bestel)
            self.assert_is_redirect(resp, self.url_bestel_stap3)

            prep.heeft_data_stap3 = True
            prep.save()
            resp = self.client.get(self.url_bestel)
            self.assert_is_redirect(resp, self.url_bestel_stap4)

    def test_bestel_stap1(self):
        self.e2e_login(self.account_sporter)

        with override_settings(TOON_SPELDEN_BESTELLEN=False):
            resp = self.client.get(self.url_bestel_stap1)
        self.assert404(resp, 'Bestellen is niet mogelijk')

        with override_settings(TOON_SPELDEN_BESTELLEN=True):
            # GET zonder SpeldenAanvraagPrep
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap1)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

            # GET zonder bogen
            self.sporterboog.delete()
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap1)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

            # POST, geen wedstrijdgeslacht, geen discipline
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1)
            self.assert404(resp, 'Onbekende discipline')

            self.voorkeuren.wedstrijd_geslacht_gekozen = True
            self.voorkeuren.wedstrijd_geslacht = 'M'
            self.voorkeuren.save()

            # POST, discipline, geen boogtype
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN'})        # Indoor
            self.assert404(resp, 'Onbekende boog')

            # POST, discipline, boogtype, geen score
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB'})          # Barebow
            self.assert404(resp, 'Slechte score')

            # goede score en datum
            datum_goed = (datetime.datetime.now() - datetime.timedelta(days=31)).strftime('%Y-%m-%d')
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '1234',
                                                                'wed_datum': datum_goed})
            self.assert_is_redirect(resp, self.url_bestel_stap2)

            # datum te ver in het verleden
            datum_bad = (datetime.datetime.now() - datetime.timedelta(days=3*365)).strftime('%Y-%m-%d')
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '1234',
                                                                'wed_datum': datum_bad})
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            # datum in de toekomst
            datum_bad = (datetime.datetime.now() + datetime.timedelta(days=31)).strftime('%Y-%m-%d')
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '1234',
                                                                'wed_datum': datum_bad})
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            # datum fout format
            datum_bad = '01-01-1900'
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '1234',
                                                                'wed_datum': datum_bad})
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            # geen datum
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '500'})
            self.assert_is_redirect(resp, self.url_bestel_stap1)

            # foute score
            with self.assert_max_queries(20):
                resp = self.client.post(self.url_bestel_stap1, {'discipline': 'IN',         # Indoor
                                                                'boogtype': 'BB',           # Barebow
                                                                'score': '0',
                                                                'wed_datum': datum_goed})
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))

            # GET met SpeldenAanvraagPrep
            with self.assert_max_queries(20):
                resp = self.client.get(self.url_bestel_stap1)
            self.assertEqual(resp.status_code, 200)
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('spelden/bestel_stap1.dtl', 'design/site_layout.dtl'))


# end of file
