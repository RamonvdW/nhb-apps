# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.utils import timezone
from Competitie.definities import DEEL_RK
from Competitie.models import CompetitieMatch, KampioenschapSporterBoog, KampioenschapTeam
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_prep
from Locatie.models import WedstrijdLocatie
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import zipfile
import os


class TestCompLaagBondFormulieren(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, Formulieren functie """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko')

    url_forms_indiv = '/bondscompetities/bk/formulieren/indiv/%s/'               # deelkamp_pk
    url_forms_teams = '/bondscompetities/bk/formulieren/teams/%s/'               # deelkamp_pk
    url_forms_download_indiv = '/bondscompetities/bk/formulieren/indiv/download/%s/%s/'   # match_pk, klasse_pk
    url_forms_download_teams = '/bondscompetities/bk/formulieren/teams/download/%s/%s/'   # match_pk, klasse_pk
    url_sr_info = '/bondscompetities/bk/wedstrijd-informatie/%s/'                # match_pk

    testdata = None
    ver_nr = 0

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()

        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in (111, 113):
            ver_nr = data.regio_ver_nrs[regio_nr][0]
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
            data.maak_rk_teams(18, ver_nr, zet_klasse=True)
        # for

        data.maak_uitslag_rk_indiv(18)
        data.maak_bk_deelnemers(18)
        data.maak_bk_teams(18)

        ver_nr = data.regio_ver_nrs[111][0]
        cls.ver = data.vereniging[ver_nr]

        cls.functie_hwl = data.functie_hwl[ver_nr]

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase O (=vereiste vaststellen klassengrenzen)
        zet_competitie_fase_bk_prep(self.testdata.comp18)

        # stel de klassengrenzen vast
        # resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        # self.e2e_dump_resp(resp)
        # self.assert_is_redirect_not_plein(resp)

        # zet de competities in fase P
        # zet_competitie_fase_bk_wedstrijden(self.testdata.comp18)
        # zet_competitie_fase_bk_wedstrijden(self.testdata.comp25)

        loc = WedstrijdLocatie(banen_18m=8,
                               banen_25m=8,
                               adres='De Spanning 1, Houtdorp')
        loc.save()
        loc.verenigingen.add(self.ver)

        # maak een BK wedstrijd aan
        self.match = CompetitieMatch(
                        competitie=self.testdata.comp18,
                        beschrijving='test wedstrijd BK',
                        datum_wanneer='2020-01-01',
                        tijd_begin_wedstrijd='10:00',
                        vereniging=self.ver,              # koppelt wedstrijd aan de vereniging
                        locatie=loc)
        self.match.save()

        # koppel de wedstrijdklassen aan de match
        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_indiv['R']:
            if klasse.is_ook_voor_rk_bk:
                match_klassen.append(klasse)
        # for
        self.match.indiv_klassen.add(*match_klassen)
        self.comp18_klassen_indiv_bk = match_klassen

        match_klassen = list()
        for klasse in self.testdata.comp18_klassen_teams['R2']:
            match_klassen.append(klasse)
        # for
        self.match.team_klassen.add(*match_klassen)
        self.comp18_klassen_teams_bk = match_klassen

        self.deelkamp18_bk = self.testdata.deelkamp18_bk
        self.deelkamp18_bk.rk_bk_matches.add(self.match.pk)

        self.deelkamp25_bk = self.testdata.deelkamp25_bk

        bad_path = '/tmp/CompLaagBond/files/'
        os.makedirs(bad_path, exist_ok=True)

        self.fpath_18_indiv = bad_path + 'template-excel-bk-indoor-indiv.xlsx'
        self.fpath_18_teams = bad_path + 'template-excel-bk-indoor-teams.xlsx'
        self.fpath_25_indiv = bad_path + 'template-excel-bk-25m1pijl-indiv.xlsx'
        self.fpath_25_teams = bad_path + 'template-excel-bk-25m1pijl-teams.xlsx'

        for fpath in (self.fpath_18_indiv, self.fpath_18_teams, self.fpath_25_indiv, self.fpath_25_teams):
            try:
                os.remove(fpath)
            except FileNotFoundError:
                pass
        # for

    @staticmethod
    def _make_bad_file(fpath):
        with zipfile.ZipFile(fpath, 'w') as xlsx:
            xlsx.writestr('hello.txt', 'Hello World')

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_forms_indiv % 999999)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_forms_teams % 999999)
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_forms_download_indiv % (999999, 999999))
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_forms_download_teams % (999999, 999999))
        self.assert_is_redirect_login(resp)

        resp = self.client.get(self.url_sr_info % 999999)
        self.assert_is_redirect_login(resp)

    def test_bad(self):
        # ingelogd als BKO Indoor

        resp = self.client.get(self.url_forms_indiv % 'xx')
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_forms_teams % '$PID')
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_forms_indiv % 999999)
        self.assert404(resp, 'Geen kampioenschap')

        # verkeerde beheerder
        resp = self.client.get(self.url_forms_teams % self.deelkamp25_bk.pk)
        self.assert404(resp, 'Niet de beheerder')

        resp = self.client.get(self.url_forms_download_indiv % (999999, 999999))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(self.url_forms_download_teams % (999999, 999999))
        self.assert404(resp, 'Wedstrijd niet gevonden')

        resp = self.client.get(self.url_forms_download_indiv % (self.match.pk, 999999))
        self.assert404(resp, 'Klasse niet gevonden')

        resp = self.client.get(self.url_forms_download_teams % (self.match.pk, 999999))
        self.assert404(resp, 'Klasse niet gevonden')

        # verander de match in een RK
        # doe dit eenvoudig door het kampioenschap om te bouwen tot een RK
        self.deelkamp18_bk.deel = DEEL_RK
        self.deelkamp18_bk.save(update_fields=['deel'])

        resp = self.client.get(self.url_forms_download_indiv % (self.match.pk, self.comp18_klassen_indiv_bk[0].pk))
        self.assert404(resp, 'Geen kampioenschap')

        resp = self.client.get(self.url_forms_download_teams % (self.match.pk, self.comp18_klassen_teams_bk[0].pk))
        self.assert404(resp, 'Geen kampioenschap')

    def test_formulieren(self):
        # bekijk het formulieren scherm voor de BKO

        url = self.url_forms_indiv % self.deelkamp18_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bko-download-bk-formulieren.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'BK individueel')
        self.assertNotContains(resp, 'BK teams')

        self.e2e_assert_other_http_commands_not_supported(url)

        url = self.url_forms_teams % self.deelkamp18_bk.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/bko-download-bk-formulieren.dtl', 'design/site_layout.dtl'))
        self.assertContains(resp, 'BK teams')
        self.assertNotContains(resp, 'BK individueel')

        self.e2e_assert_other_http_commands_not_supported(url)

    def test_download(self):
        # BKO download een ingevuld BK programma

        indiv_klasse = KampioenschapSporterBoog.objects.filter(kampioenschap=self.deelkamp18_bk)[0].indiv_klasse
        team_klasse = KampioenschapTeam.objects.filter(kampioenschap=self.deelkamp18_bk)[0].team_klasse

        url = self.url_forms_download_indiv % (self.match.pk, indiv_klasse.pk)
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert200_is_bestand_xlsx(resp)

        # niet bestaand BK programma
        with override_settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan BK programma niet vinden')

        # kapot BK programma
        self._make_bad_file(self.fpath_18_indiv)
        with override_settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan BK programma niet openen')

        url = self.url_forms_download_teams % (self.match.pk, team_klasse.pk)
        with self.assert_max_queries(28):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert200_is_bestand_xlsx(resp)

        # niet bestaand BK programma
        with override_settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan BK programma niet vinden')

        # kapot BK programma
        self._make_bad_file(self.fpath_18_teams)
        with override_settings(INSTALL_PATH='/tmp'):
            resp = self.client.get(url)
        self.assert404(resp, 'Kan BK programma niet openen')

    def test_sr_info(self):
        # HWL kan toegekende SR zien
        self.e2e_wissel_naar_functie(self.functie_hwl)

        url = self.url_sr_info % self.match.pk
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/hwl-bk-match-info.dtl', 'design/site_layout.dtl'))

        # SR nodig
        self.match.aantal_scheids = 1
        self.match.save(update_fields=['aantal_scheids'])

        # niet bestaande match
        resp = self.client.get(self.url_sr_info % 999999)
        self.assert404(resp, "Wedstrijd niet gevonden")

        # verkeerde HWL
        self.e2e_wissel_naar_functie(self.testdata.functie_hwl[self.ver.ver_nr + 1])
        url = self.url_sr_info % self.match.pk
        resp = self.client.get(url)
        self.assert404(resp, 'Niet de beheerder')

# end of file
