# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEELNAME_NEE
from Competitie.models import KampioenschapSporterBoog
from Competitie.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagBondCliImportUitslagBkTeams(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, import van de BK uitslag """

    url_klassengrenzen_teams_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    real_testfile_pdf_25m1pijl = 'CompLaagBond/management/testfiles/test_bk-25m1pijl-teams_pdf.pdf'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for ver_nr in cls.testdata.regio_ver_nrs[cls.regio_nr][:2]:
            print('ver:', ver_nr)
            data.maak_rk_deelnemers(25, ver_nr, cls.regio_nr)
            #data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

            per_team = 3 if ver_nr == 4092 else 4
            data.maak_rk_teams(25, ver_nr, per_team, limit_teamtypen=['C'])
        # for

        # bepaal team klasse

        # meld een paar deelnemers af
        for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand='25',
                                                                 sporterboog__sporter__lid_nr__in=(301846, 301883)):
            deelnemer.deelname = DEELNAME_NEE
            deelnemer.save(update_fields=['deelname'])
        # for

    def setUp(self):

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')

        # zet de competitie in fase J (=vereiste vaststellen klassengrenzen)
        #zet_competitie_fase_rk_prep(self.testdata.comp18)
        zet_competitie_fase_rk_prep(self.testdata.comp25)

        # stel de klassengrenzen vast
        resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)

        #resp = self.client.post(self.url_klassengrenzen_teams_vaststellen % self.testdata.comp18.pk)
        #self.assert_is_redirect_not_plein(resp)

        self.testdata.maak_bk_teams(25)

        # zet de competities in fase P
        #zet_competitie_fase_bk_wedstrijden(self.testdata.comp18)
        zet_competitie_fase_bk_wedstrijden(self.testdata.comp25)

    # def test_excel_25m(self):
    #     # bestand NOK
    #     f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv', 'bestand')
    #     self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())
    #
    #     f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv',
    #                                          self.real_testfile_excel_25m1pijl,
    #                                          '--dryrun', '--verbose')
    #     # print('\nf1: %s' % f1.getvalue())
    #     # print('\nf2: %s' % f2.getvalue())
    #     self.assertTrue('[ERROR] Probleem met scores op regel 26' in f1.getvalue())
    #     self.assertTrue('[ERROR] Geen BK deelnemer op regel 24: 123456' in f1.getvalue())
    #     self.assertTrue('[ERROR] Te hoge scores op regel 22: 251' in f1.getvalue())
    #
    #     # echte import
    #     self.run_management_command('import_uitslag_bk_25m1pijl_indiv',
    #                                 self.real_testfile_excel_25m1pijl)
    #     # print('\nf1: %s' % f1.getvalue())
    #     # print('\nf2: %s' % f2.getvalue())
    #
    # def test_excel_18m(self):
    #     # file NOK
    #     f1, f2 = self.run_management_command('import_uitslag_bk_indoor_indiv', 'bestand')
    #     self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())
    #
    #     f1, f2 = self.run_management_command('import_uitslag_bk_indoor_indiv',
    #                                          self.real_testfile_excel_indoor,
    #                                          '--dryrun', '--verbose')
    #     _ = (f1, f2)
    #     # print('f1:', f1.getvalue())
    #     # print('f2:', f2.getvalue())
    #     self.assertTrue('hoort in klasse: Longbow klasse 2' in f1.getvalue())
    #     self.assertTrue('[ERROR] Geen BK deelnemer op regel 25: 123456' in f1.getvalue())
    #     self.assertTrue("[ERROR] Probleem met scores op regel 27: 'n/a' en 'n/a'" in f1.getvalue())
    #     self.assertTrue("[INFO] Klasse: Recurve klasse 6" in f2.getvalue())
    #     self.assertTrue("[WARNING] Regel 26 wordt overgeslagen (geen scores)" in f2.getvalue())
    #     self.assertTrue("Volgorde=1, Rank=1, Q-scores=204, 228, deelnemer=[301849]" in f2.getvalue())
    #
    #     f1, f2 = self.run_management_command('import_uitslag_bk_indoor_indiv', self.real_testfile_excel_indoor)
    #     _ = (f1, f2)
    #     # print('f1:', f1.getvalue())
    #     # print('f2:', f2.getvalue())
    #     kampioen = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
    #                                                     sporterboog__sporter__lid_nr=301849)
    #     self.assertEqual(kampioen.result_rank, 1)
    #     self.assertEqual(kampioen.result_score_1, 204)
    #     self.assertEqual(kampioen.result_score_2, 228)
    #     self.assertEqual(kampioen.result_counts, '')        # alleen voor 25m1pijl
    #
    # def test_ianseo_html_25m(self):
    #     # bestand NOK
    #     f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html', 'bestand')
    #     self.assertTrue('[ERROR] Kan het html bestand niet openen' in f1.getvalue())
    #
    #     f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html',
    #                                          self.real_testfile_html_25m1pijl,
    #                                          '--dryrun', '--verbose')
    #     # print('f1:', f1.getvalue())
    #     # print('f2:', f2.getvalue())
    #
    #     f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html',
    #                                          self.real_testfile_html_25m1pijl)
    #     # print('f1:', f1.getvalue())
    #     # print('f2:', f2.getvalue())
    #
    def test_ianseo_pdf_25m(self):
        # bestand NOK
        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_teams_ianseo-pdf', 'bestand')
        self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_teams_ianseo-pdf',
                                             self.real_testfile_pdf_25m1pijl,
                                             '--verbose')
        print('f1:', f1.getvalue())
        print('f2:', f2.getvalue())
        #self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())


# end of file
