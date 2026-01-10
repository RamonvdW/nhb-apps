# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import RegiocompetitieSporterBoog
from Competitie.operations import competities_aanmaken
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_prep
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompBeheerStats(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module Statistiek """

    test_after = ('BasisTypen', 'Functie', 'Competitie.tests.test_overzicht')

    url_kies = '/bondscompetities/'
    url_statistiek = '/bondscompetities/beheer/statistiek/'

    testdata = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities(2020)
        ver_nr = data.regio_ver_nrs[101][1]
        data.maak_inschrijvingen_regiocompetitie(18, ver_nr)
        data.maak_inschrijvingen_regiocompetitie(25, ver_nr)
        data.maak_inschrijvingen_regio_teamcompetitie(18, ver_nr)
        data.maak_inschrijvingen_regio_teamcompetitie(25, ver_nr)

        # zet de teamcompetitie uit in een regio
        regio_nr = 112
        for deelcomp in (data.deelcomp18_regio[regio_nr], data.deelcomp25_regio[regio_nr]):
            deelcomp.regio_organiseert_teamcompetitie = False
            deelcomp.save(update_fields=['regio_organiseert_teamcompetitie'])
        # for

        # verwijder all sporters in een regio
        Sporter.objects.filter(bij_vereniging__regio__regio_nr=103).all().delete()

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def test_stats_bb(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        # controleer dat het "kies" scherm het kaartje statistiek bevat
        resp = self.client.get(self.url_kies)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertIn(self.url_statistiek, urls)

        # haal de statistiek pagina op
        with self.assert_max_queries(56):
            resp = self.client.get(self.url_statistiek)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/statistiek.dtl', 'design/site_layout.dtl'))

        # cornercase: nul alle inschrijvingen
        RegiocompetitieSporterBoog.objects.all().delete()
        with self.assert_max_queries(56):
            resp = self.client.get(self.url_statistiek)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/statistiek.dtl', 'design/site_layout.dtl'))

        # anon test
        self.e2e_logout()
        resp = self.client.get(self.url_statistiek)
        self.assert403(resp)

    def test_stats_rcl(self):
        regio_nr = 111
        self.e2e_login_and_pass_otp(self.testdata.comp18_account_rcl[regio_nr])
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_rcl[regio_nr])

        # controleer dat het "kies" scherm het kaartje statistiek bevat
        resp = self.client.get(self.url_kies)
        urls = self.extract_all_urls(resp, skip_menu=True)
        self.assertIn(self.url_statistiek, urls)

        # maak nog een competitie aan (deze wordt niet getoond)
        competities_aanmaken(jaar=2018)

        # haal de statistiek pagina op
        with self.assert_max_queries(56):
            resp = self.client.get(self.url_statistiek)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/statistiek.dtl', 'design/site_layout.dtl'))

        # haal de (lege) statistiek pagina op als geen competitie in fase C of later is
        zet_competitie_fase_regio_prep(self.testdata.comp18)
        zet_competitie_fase_regio_prep(self.testdata.comp25)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_statistiek)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/statistiek.dtl', 'design/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(self.url_statistiek)

# end of file
