# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Functie.models import maak_functie
from NhbStructuur.models import NhbRegio, NhbVereniging
from Competitie.models import DeelCompetitie, CompetitieKlasse, LAAG_RK, DeelcompetitieKlasseLimiet, KampioenschapSchutterBoog
from Competitie.test_competitie import maak_competities_en_zet_fase_b
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestVerenigingLijstRK(E2EHelpers, TestCase):

    """ Tests voor de Vereniging applicatie, functies voor de HWL """

    test_after = ('BasisTypen', 'NhbStructuur', 'Functie', 'Sporter', 'Competitie')

    url_lijst_rk = '/vereniging/lijst-rayonkampioenschappen/%s/'  # deelcomp_pk

    testdata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self._create_competitie()

        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1000"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver1 = ver

        # maak de HWL functie
        self.functie_hwl = maak_functie("HWL test", "HWL")
        self.functie_hwl.nhb_ver = ver
        self.functie_hwl.save()

        self.functie_wl = maak_functie("WL test", "WL")
        self.functie_wl.nhb_ver = ver
        self.functie_wl.save()

        # maak het lid aan dat HWL wordt
        sporter = Sporter()
        sporter.lid_nr = 100001
        sporter.geslacht = "M"
        sporter.voornaam = "Ramon"
        sporter.achternaam = "de Tester"
        sporter.email = "rdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()

        self.account_beheerder = self.e2e_create_account(sporter.lid_nr,
                                                         sporter.email,
                                                         sporter.voornaam,
                                                         accepteer_vhpg=True)
        self.functie_hwl.accounts.add(self.account_beheerder)
        self.functie_wl.accounts.add(self.account_beheerder)

        sporter.account = self.account_beheerder
        sporter.save()
        self.sporter_100001 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100001,
                                  boogtype=BoogType.objects.get(afkorting='R'),
                                  voor_wedstrijd=True)
        sporterboog.save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_r1,
                                  sporterboog=sporterboog,
                                  klasse=self.klasse_r,
                                  bij_vereniging=ver).save()

        # maak een test vereniging
        ver = NhbVereniging()
        ver.naam = "Grote Club"
        ver.ver_nr = "1001"
        ver.regio = NhbRegio.objects.get(regio_nr=111)
        # secretaris kan nog niet ingevuld worden
        ver.save()
        self.nhbver2 = ver

        sporter = Sporter()
        sporter.lid_nr = 100002
        sporter.geslacht = "V"
        sporter.voornaam = "Petra"
        sporter.achternaam = "de Tester"
        sporter.email = "pdetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100002 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100002,
                                  boogtype=BoogType.objects.get(afkorting='C'),
                                  voor_wedstrijd=True)
        sporterboog.save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_r1,
                                  sporterboog=sporterboog,
                                  klasse=self.klasse_c,
                                  bij_vereniging=ver).save()

        sporter = Sporter()
        sporter.lid_nr = 100003
        sporter.geslacht = "M"
        sporter.voornaam = "Pedro"
        sporter.achternaam = "de Tester"
        sporter.email = "podetester@gmail.not"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.bij_vereniging = ver
        sporter.save()
        self.sporter_100003 = sporter

        sporterboog = SporterBoog(sporter=self.sporter_100003,
                                  boogtype=BoogType.objects.get(afkorting='C'),
                                  voor_wedstrijd=True)
        sporterboog.save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_r1,
                                  sporterboog=sporterboog,
                                  klasse=self.klasse_c,
                                  bij_vereniging=ver,
                                  rank=100).save()

        # zet een cut
        DeelcompetitieKlasseLimiet(deelcompetitie=self.deelcomp_r1,
                                   klasse=self.klasse_c,
                                   limiet=20).save()

    def _create_competitie(self):
        # BB worden
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')

        self.assertEqual(CompetitieKlasse.objects.count(), 0)
        self.comp_18, self.comp_25 = maak_competities_en_zet_fase_b()

        self.klasse_r = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                        indiv__boogtype__afkorting='R',
                                                        min_ag__gt=0.0)[0]

        self.klasse_ib = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                         indiv__boogtype__afkorting='IB')[0]

        self.klasse_c = CompetitieKlasse.objects.filter(competitie=self.comp_18,
                                                        indiv__boogtype__afkorting='C',
                                                        min_ag__gt=0.0)[0]

        self.deelcomp_r1 = DeelCompetitie.objects.get(laag=LAAG_RK,
                                                      nhb_rayon__rayon_nr=1,
                                                      competitie__afstand=18)

    def test_hwl_lijst_rk(self):
        self.e2e_login_and_pass_otp(self.account_beheerder)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        # haal de RK lijst op voordat er een deelnemerslijst is
        url = self.url_lijst_rk % self.deelcomp_r1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found/allowed

        # zet de deelnemerslijst (fake)
        self.deelcomp_r1.heeft_deelnemerslijst = True
        self.deelcomp_r1.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

        # voeg een extra deelnemer toe in een latere wedstrijdklasse
        # dit voor code coverage
        self.sporterboog_ib = SporterBoog(sporter=self.sporter_100001,
                                          boogtype=BoogType.objects.get(afkorting='IB'),
                                          voor_wedstrijd=True)
        self.sporterboog_ib.save()

        KampioenschapSchutterBoog(deelcompetitie=self.deelcomp_r1,
                                  sporterboog=self.sporterboog_ib,
                                  klasse=self.klasse_ib,
                                  bij_vereniging=self.functie_hwl.nhb_ver).save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

    def test_wl_lijst_rk(self):
        self.e2e_login_and_pass_otp(self.account_beheerder)
        self.e2e_wissel_naar_functie(self.functie_wl)
        self.e2e_check_rol('WL')

        # zet de deelnemerslijst (fake)
        self.deelcomp_r1.heeft_deelnemerslijst = True
        self.deelcomp_r1.save()

        url = self.url_lijst_rk % self.deelcomp_r1.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('vereniging/lijst-rk-selectie.dtl', 'plein/site_layout.dtl'))

    def test_bad_lijst_rk(self):
        # anon
        self.client.logout()

        url = self.url_lijst_rk % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.functie_hwl)
        self.e2e_check_rol('HWL')

        url = self.url_lijst_rk % 999999
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp)     # 404 = Not found/allowed

# end of file
