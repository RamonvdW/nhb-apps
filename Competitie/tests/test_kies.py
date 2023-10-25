# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.test import TestCase
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Sporter.models import Sporter
from Vereniging.models import Vereniging
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestCompetitieKies(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, pagina Kies """

    url_kies = '/bondscompetities/'

    def setUp(self):
        self.account_admin = self.e2e_create_account_admin()

        # deze test is afhankelijk van de standaard regio's
        regio = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio)
        ver.save()

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save()

        # maak een volwassen test lid aan (komt in groep met klasse onbekend)
        sporter = Sporter(
                    lid_nr=100001,
                    geslacht="M",
                    voornaam="Ramon",
                    achternaam="de Tester",
                    email="rdetester@gmail.not",
                    geboorte_datum=datetime.date(year=1972, month=3, day=4),
                    sinds_datum=datetime.date(year=2010, month=11, day=12),
                    bij_vereniging=ver)
        self.account_lid = sporter.account = self.e2e_create_account(sporter.lid_nr, sporter.email, sporter.voornaam)
        sporter.save()
        self.sporter_100001 = sporter

    def test_bb(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        # opstarten
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        now = timezone.now()

        begin_jaar = now.year - 1
        maak_competities_en_zet_fase_c(startjaar=begin_jaar)

        begin_jaar = now.year
        comp_18, comp_25 = maak_competities_en_zet_fase_c(startjaar=begin_jaar)
        zet_competitie_fases(comp_25, 'A', 'A')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

        # afsluiten
        zet_competitie_fases(comp_18, 'Q', 'Q')
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

    def test_anon(self):
        self.client.logout()

        now = timezone.now()
        begin_jaar = now.year
        comp_18, comp_25 = maak_competities_en_zet_fase_c(startjaar=begin_jaar)
        zet_competitie_fases(comp_25, 'A', 'A')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

    def test_sporter(self):
        self.e2e_login(self.account_lid)

        now = timezone.now()
        begin_jaar = now.year
        maak_competities_en_zet_fase_c(startjaar=begin_jaar)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))

    def test_hwl(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        now = timezone.now()
        begin_jaar = now.year
        maak_competities_en_zet_fase_c(startjaar=begin_jaar)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_kies)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/kies.dtl', 'plein/site_layout.dtl'))


# end of file
