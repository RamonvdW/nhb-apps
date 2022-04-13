# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import CompetitieMatch
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import zipfile
import os


class TestCompRayonFormulieren(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, Formulieren functie """

    test_after = ('Competitie.test_fase', 'CompLaagRayon.test_teams_rko', 'CompLaagRayon.test_teams_rko')

    url_forms = '/bondscompetities/rk/download-formulier/%s/'                             #  wedstrijd_pk
    url_forms_download_indiv = '/bondscompetities/rk/download-formulier-indiv/%s/%s/'     # wedstrijd_pk, klasse_pk
    url_forms_download_teams = '/bondscompetities/rk/download-formulier-teams/%s/%s/'     # wedstrijd_pk, klasse_pk

    testdata = None
    regio_nr = 113
    rayon_nr = 4
    ver_nr = 0

    @classmethod
    def setUpTestData(cls):
        print('CompLaagRayon.test_formulieren: populating testdata start')
        s1 = timezone.now()

        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

        cls.ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][0]
        cls.ver = cls.testdata.vereniging[cls.ver_nr]

        cls.testdata.maak_inschrijvingen_regiocompetitie(18, cls.ver_nr)
        cls.testdata.maak_rk_deelnemers(18, cls.ver_nr, cls.regio_nr)
        cls.testdata.maak_inschrijvingen_rk_teamcompetitie(18, cls.ver_nr)

        # TODO: competitie doorzetten naar fase K zodat de team.klasse ingevuld is

        s2 = timezone.now()
        d = s2 - s1
        print('CompLaagRayon.test_formulieren: populating testdata took %s seconds' % d.seconds)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        # maak een RK wedstrijd aan
        self.match = CompetitieMatch(
                            competitie=self.testdata.comp18,
                            beschrijving='test wedstrijd RK',
                            datum_wanneer='2020-01-01',
                            tijd_begin_wedstrijd='10:00',
                            vereniging=self.ver)            # koppelt wedstrijd aan de vereniging
        # TODO: locatie koppelen
        self.match.save()

        self.deelcomp18_rk = self.testdata.deelcomp18_rk[self.rayon_nr]
        self.deelcomp18_rk.rk_bk_matches.add(self.match.pk)

        self.deelcomp25_rk = self.testdata.deelcomp25_rk[self.rayon_nr]

        bad_path = '/tmp/CompLaagRayon/files/'
        os.makedirs(bad_path, exist_ok=True)

        self.xlsm_fpath_18_indiv = bad_path + 'template-excel-rk-indoor-indiv.xlsm'
        self.xlsm_fpath_18_teams = bad_path + 'template-excel-rk-indoor-teams.xlsm'
        self.xlsm_fpath_25_indiv = bad_path + 'template-excel-rk-25m1pijl-indiv.xlsm'
        self.xlsm_fpath_25_teams = bad_path + 'template-excel-rk-25m1pijl-teams.xlsm'

        for fpath in (self.xlsm_fpath_18_indiv, self.xlsm_fpath_18_teams,
                      self.xlsm_fpath_25_indiv, self.xlsm_fpath_25_teams):
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
        url = self.url_forms % self.match.pk

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
        self.assert_template_used(resp, ('complaagrayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen indiv klassen
        self.match.indiv_klassen.set([self.testdata.comp18_klassen_indiv['R'][0],
                                      self.testdata.comp18_klassen_indiv['R'][-1]])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # indiv + teams klassen
        self.match.team_klassen.set([self.testdata.comp18_klassen_team['R2'][0],
                                     self.testdata.comp18_klassen_team['R2'][-1]])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # alleen teams klassen
        self.match.indiv_klassen.set([])
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_template_used(resp, ('complaagrayon/hwl-download-rk-formulier.dtl', 'plein/site_layout.dtl'))
        self.assert_html_ok(resp)

        # wedstrijd niet in een plan
        self.deelcomp18_rk.rk_bk_matches.remove(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

        # 25m1p plan
        self.deelcomp25_rk.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.deelcomp25_rk.rk_bk_matches.remove(self.match.pk)

        # wedstrijd van een niet-RK deelcompetitie
        self.testdata.deelcomp18_bk.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms % 'xxx')
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_download_indiv(self):
        klasse = self.testdata.comp18_klassen_indiv['R'][0]
        url = self.url_forms_download_indiv % (self.match.pk, klasse.pk)

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
        self._make_bad_xlsm_file(self.xlsm_fpath_18_indiv)
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet openen')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_indiv % (999999, 'xxx'))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # niet bestaande klasse
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_indiv % (self.match.pk, 'xxx'))
        self.assert404(resp, 'Klasse niet gevonden')

        # wedstrijd niet in een plan
        self.deelcomp18_rk.rk_bk_matches.remove(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen RK wedstrijd')

        # wedstrijd van een niet-RK deelcompetitie
        self.testdata.deelcomp18_bk.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

    def test_download_teams(self):
        klasse = self.testdata.comp18_klassen_team['R2'][0]
        url = self.url_forms_download_teams % (self.match.pk, klasse.pk)

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
        self._make_bad_xlsm_file(self.xlsm_fpath_18_teams)
        with self.settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan RK programma niet openen')

        # niet bestaande wedstrijd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_teams % (999999, 'xxx'))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # niet bestaande klasse
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_forms_download_teams % (self.match.pk, 'xxx'))
        self.assert404(resp, 'Klasse niet gevonden')

        # wedstrijd niet in een plan
        self.deelcomp18_rk.rk_bk_matches.remove(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Geen RK wedstrijd')

        # wedstrijd van een niet-RK deelcompetitie
        plan = self.testdata.deelcomp18_bk.rk_bk_matches.add(self.match.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert404(resp, 'Verkeerde competitie')

# end of file
