# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Wedstrijden.models import CompetitieWedstrijd
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import zipfile
import time
import os


class TestCompRayonFormulieren(E2EHelpers, TestCase):

    """ tests voor de CompRayon applicatie, Formulieren functie """

    test_after = ('Competitie.test_fase', 'CompRayon.test_teams_rko', 'CompRayon.test_teams_rko')

    url_forms = '/bondscompetities/rk/download-formulier/%s/'                             #  wedstrijd_pk
    url_forms_download_indiv = '/bondscompetities/rk/download-formulier-indiv/%s/%s/'     # wedstrijd_pk, klasse_pk
    url_forms_download_teams = '/bondscompetities/rk/download-formulier-teams/%s/%s/'     # wedstrijd_pk, klasse_pk

    testdata = None
    regio_nr = 113
    rayon_nr = 4
    ver_nr = 0

    @classmethod
    def setUpTestData(cls):
        print('CompRayon.test_formulieren: populating testdata start')
        s1 = timezone.now()

        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr]
        cls.ver = cls.testdata.vereniging[cls.ver_nr]

        cls.testdata.maak_inschrijvingen_regiocompetitie(18, cls.ver_nr)
        cls.testdata.maak_rk_deelnemers(18, cls.ver_nr, cls.regio_nr)
        cls.testdata.maak_inschrijvingen_rk_teamcompetitie(18, cls.ver_nr)

        # TODO: competitie doorzetten naar fase K zodat de team.klasse ingevuld is

        s2 = timezone.now()
        d = s2 - s1
        print('CompRayon.test_formulieren: populating testdata took %s seconds' % d.seconds)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een RK wedstrijd aan
        self.wedstrijd = CompetitieWedstrijd(
                            beschrijving='test wedstrijd RK',
                            datum_wanneer='2020-01-01',
                            tijd_begin_aanmelden='09:00',
                            tijd_begin_wedstrijd='10:00',
                            tijd_einde_wedstrijd='16:00',
                            vereniging=self.ver)            # koppelt wedstrijd aan de vereniging
        # TODO: locatie koppelen
        self.wedstrijd.save()

        self.deelcomp18_rk_wedstrijden_plan = self.testdata.deelcomp18_rk[self.rayon_nr].plan
        self.deelcomp18_rk_wedstrijden_plan.wedstrijden.add(self.wedstrijd.pk)

        self.deelcomp25_rk_wedstrijden_plan = self.testdata.deelcomp25_rk[self.rayon_nr].plan

        bad_path = '/tmp/CompRayon/files/'
        os.makedirs(bad_path, exist_ok=True)

        self.xlsm_fpath_indiv = bad_path + 'template-excel-rk-indiv.xlsm'
        self.xlsm_fpath_teams = bad_path + 'template-excel-rk-teams.xlsm'

        for fpath in (self.xlsm_fpath_indiv, self.xlsm_fpath_teams):
            try:
                os.remove(fpath)
            except FileNotFoundError:
                pass
        # for

    @staticmethod
    def _make_bad_xlsm_file(fpath):
        with zipfile.ZipFile(fpath, 'w') as xlsm:
            xlsm.writestr('hello.txt', 'Hello World')

    def test_get_forms(self):
        url = self.url_forms % self.wedstrijd.pk

        # ophalen zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        # geen klassen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('comprayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen indiv klassen
        self.wedstrijd.indiv_klassen.set([self.testdata.comp18_klassen_indiv['R'][0].indiv,
                                          self.testdata.comp18_klassen_indiv['R'][-1].indiv])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('comprayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # indiv + teams klassen
        self.wedstrijd.team_klassen.set([self.testdata.comp18_klassen_team['R'][0].team,
                                         self.testdata.comp18_klassen_team['R'][-1].team])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('comprayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen teams klassen
        self.wedstrijd.indiv_klassen.set([])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('comprayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wedstrijd niet in een plan
        self.deelcomp18_rk_wedstrijden_plan.wedstrijden.remove(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen wedstrijden plan')

        # 25m1p plan
        self.deelcomp25_rk_wedstrijden_plan.wedstrijden.add(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.deelcomp25_rk_wedstrijden_plan.wedstrijden.remove(self.wedstrijd.pk)

        # wedstrijd van een niet-RK deelcompetitie
        plan = self.testdata.deelcomp18_bk.plan
        plan.wedstrijden.add(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms % 'xxx')
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_download_indiv(self):
        klasse = self.testdata.comp18_klassen_indiv['R'][0]
        url = self.url_forms_download_indiv % (self.wedstrijd.pk, klasse.pk)

        # ophalen zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_file(resp)

        # niet bestaand RK programma
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet vinden')

        # kapot RK programma
        self._make_bad_xlsm_file(self.xlsm_fpath_indiv)
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet openen')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_indiv % (999999, 'xxx'))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # niet bestaande klasse
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_indiv % (self.wedstrijd.pk, 'xxx'))
        self.assert404(resp, 'Klasse niet gevonden')

        # wedstrijd niet in een plan
        self.deelcomp18_rk_wedstrijden_plan.wedstrijden.remove(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen wedstrijden plan')

        # wedstrijd van een niet-RK deelcompetitie
        plan = self.testdata.deelcomp18_bk.plan
        plan.wedstrijden.add(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

    def test_download_teams(self):
        klasse = self.testdata.comp18_klassen_team['R'][0]
        url = self.url_forms_download_teams % (self.wedstrijd.pk, klasse.pk)

        # ophalen zonder inlog
        self.client.logout()
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp)

        self.e2e_login_and_pass_otp(self.testdata.account_hwl[self.ver_nr])
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver_nr])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert200_file(resp)

        # niet bestaand RK programma
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet vinden')

        # kapot RK programma
        self._make_bad_xlsm_file(self.xlsm_fpath_teams)
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet openen')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_teams % (999999, 'xxx'))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # niet bestaande klasse
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_teams % (self.wedstrijd.pk, 'xxx'))
        self.assert404(resp, 'Klasse niet gevonden')

        # wedstrijd niet in een plan
        self.deelcomp18_rk_wedstrijden_plan.wedstrijden.remove(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen wedstrijden plan')

        # wedstrijd van een niet-RK deelcompetitie
        plan = self.testdata.deelcomp18_bk.plan
        plan.wedstrijden.add(self.wedstrijd.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')



# end of file
