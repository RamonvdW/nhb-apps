# -*- coding: utf-8 -*-

#  Copyright (c) 2024-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.models import TemplateCompetitieIndivKlasse, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from Competitie.test_utils.tijdlijn import zet_competitie_fases
from CompLaagRegio.models import RegioComp
from CompLaagBond.models import KampBK
from Functie.tests.helpers import maak_functie
from Geo.models import Rayon, Regio
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
from Vereniging.models import Vereniging
import datetime


class TestCompBeheerTijdlijn(E2EHelpers, TestCase):

    """ tests voor de CompBeheer applicatie, module Tijdlijn """

    test_after = ('Competitie.tests.test_tijdlijn',)

    url_tijdlijn = '/bondscompetities/beheer/%s/tijdlijn/'     # comp_pk

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def setUp(self):
        self.comp = Competitie.objects.create(
                        begin_jaar=2000,
                        afstand=25,
                        beschrijving='test',
                        klassengrenzen_vastgesteld=True)
        self.comp.refresh_from_db()     # echte datums in plaats van strings

        indiv = TemplateCompetitieIndivKlasse.objects.first()
        teamtype = TeamType.objects.first()
        self.comp.teamtypen.add(teamtype)

        CompetitieIndivKlasse(competitie=self.comp, volgorde=1, boogtype=indiv.boogtype, min_ag=0.0).save()
        CompetitieTeamKlasse(competitie=self.comp, volgorde=1, min_ag=0.0, team_type=teamtype).save()

        rayon_3 = Rayon.objects.get(rayon_nr=3)
        regio_111 = Regio.objects.get(regio_nr=111)
        regio_112 = Regio.objects.get(regio_nr=112)
        regio_113 = Regio.objects.get(regio_nr=113)

        self.func_bko = maak_functie("BKO", "BKO")

        self.func_rko = maak_functie("RKO 3", "RKO")
        self.func_rko.rayon = rayon_3
        self.func_rko.save()

        self.func_rcl = maak_functie("RCL 112", "RCL")
        self.func_rcl.regio = regio_112
        self.func_rcl.save()

        ver = Vereniging.objects.create(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=regio_111)        # HWL ziet team fase C

        self.func_hwl = maak_functie('HWL test', 'HWL')
        self.func_hwl.vereniging = ver
        self.func_hwl.save()

        self.func_wl = maak_functie('WL test', 'WL')
        self.func_wl.vereniging = ver
        self.func_wl.save()

        date_future = (timezone.now() + datetime.timedelta(days=30)).date()
        date_past = (timezone.now() - datetime.timedelta(days=2)).date()

        # 111 is nog in fase C (de HWL ziet deze)
        RegioComp.objects.create(
                competitie=self.comp,
                regio=regio_111,
                functie=self.func_bko,
                huidige_team_ronde=0,
                begin_fase_D=date_future)

        # 112 is in fase D (de RCL ziet deze)
        self.deelcomp_112 = RegioComp.objects.create(
                competitie=self.comp,
                regio=regio_112,
                functie=self.func_rcl,
                huidige_team_ronde=0,
                begin_fase_D=date_past)

        # 113 is in fase F
        RegioComp.objects.create(
                competitie=self.comp,
                regio=regio_113,
                functie=self.func_bko,
                huidige_team_ronde=1,
                begin_fase_D=date_past)

        KampBK.objects.create(
                competitie=self.comp,
                functie=self.func_bko)

    def test_alle_fases(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()

        url = self.url_tijdlijn % self.comp.pk

        sequence = 'ABCDFGJKLNOPQZ'      # noqa
        for fase in sequence:
            zet_competitie_fases(self.comp, fase, fase)

            with self.assert_max_queries(20):
                resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)  # 200 = OK
            self.assert_html_ok(resp)
            self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))
        # for

    def test_team_fases(self):
        # check speciaal gedrag in fase C, D, en F van de teamcompetitie
        zet_competitie_fases(self.comp, 'F', 'F')
        url = self.url_tijdlijn % self.comp.pk

        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        # test als BKO
        self.e2e_wissel_naar_functie(self.func_bko)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))

        # test als RKO
        self.e2e_wissel_naar_functie(self.func_rko)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))

        # test als RCL, fase D
        self.e2e_wissel_naar_functie(self.func_rcl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))

        # test als HWL
        self.e2e_wissel_naar_functie(self.func_hwl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))

        # test als WL
        self.e2e_wissel_naar_functie(self.func_wl)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('compbeheer/tijdlijn.dtl', 'design/site_layout.dtl'))

        # corner case
        resp = self.client.get(self.url_tijdlijn % 99999)
        self.assert404(resp, 'Competitie niet gevonden')


# end of file
