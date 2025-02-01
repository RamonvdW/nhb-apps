# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import TeamType
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieTeam
from Functie.definities import Rol
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime


class TestCompetitieInfo(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, module Informatie over de Competitie """

    url_info = '/bondscompetities/info/'
    url_info_teams = '/bondscompetities/info/teams/'

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # deze test is afhankelijk van de standaard regio's
        regio = Regio.objects.get(regio_nr=101)

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio)
        ver.save()

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

        self.account_geen_lid = self.e2e_create_account('geen_lid', 'geen_lid@gmail.com', 'Testertje')

        # stel een team op voor de Indoor
        competitie = Competitie(
                        beschrijving='Indoor 2000/2001',
                        afstand='18',
                        begin_jaar=2000)
        competitie.save()

        functie = maak_functie('maak niet uit', Rol.ROL_BB)

        regiocompetitie = Regiocompetitie(
                            competitie=competitie,
                            regio=regio,
                            functie=functie,
                            regio_organiseert_teamcompetitie=True,
                            regio_heeft_vaste_teams=True)
        regiocompetitie.save()
        self.regiocomp_18 = regiocompetitie

        team_type = TeamType.objects.filter(afkorting='C').first()

        team = RegiocompetitieTeam(
                        regiocompetitie=regiocompetitie,
                        vereniging=ver,
                        volg_nr=1,
                        team_type=team_type)
        team.save()

        # stel een team op voor de 25m1pijl
        competitie = Competitie(
                        beschrijving='25m1pijl 2000/2001',
                        afstand='25',
                        begin_jaar=2000)
        competitie.save()

        functie = maak_functie('maak niet uit', Rol.ROL_BB)

        regiocompetitie = Regiocompetitie(
                            competitie=competitie,
                            regio=regio,
                            functie=functie,
                            regio_organiseert_teamcompetitie=True,
                            regio_heeft_vaste_teams=True)
        regiocompetitie.save()
        self.regiocomp_25 = regiocompetitie

        team_type = TeamType.objects.filter(afkorting='C').first()

        team = RegiocompetitieTeam(
                        regiocompetitie=regiocompetitie,
                        vereniging=ver,
                        volg_nr=1,
                        team_type=team_type)
        team.save()

    def test_info(self):
        # anon
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # geen lid
        self.e2e_login(self.account_geen_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.client.logout()
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # inactief
        self.sporter_100001.bij_vereniging = None
        self.sporter_100001.save(update_fields=['bij_vereniging'])
        self.client.logout()
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-competitie.dtl', 'plein/site_layout.dtl'))

        # redirect oud naar nieuw
        resp = self.client.get('/bondscompetities/info/leeftijden/')
        self.assert_is_redirect(resp, '/sporter/leeftijden/')

    def test_info_teams(self):
        # anon
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info_teams)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-teamcompetitie.dtl', 'plein/site_layout.dtl'))

        # geen lid
        self.e2e_login(self.account_geen_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info_teams)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-teamcompetitie.dtl', 'plein/site_layout.dtl'))

        # sporter
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info_teams)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-teamcompetitie.dtl', 'plein/site_layout.dtl'))

        # inactief
        self.sporter_100001.bij_vereniging = None
        self.sporter_100001.save(update_fields=['bij_vereniging'])
        self.client.logout()
        self.e2e_login(self.account_lid)
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_info_teams)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('competitie/info-teamcompetitie.dtl', 'plein/site_layout.dtl'))

# end of file
