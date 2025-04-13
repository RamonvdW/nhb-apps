# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEELNAME_NEE
from Competitie.models import KampioenschapSporterBoog
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagBondCliImportUitslagBkTeams(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, import van de BK uitslag """

    url_vaststellen = '/bondscompetities/beheer/%s/doorzetten/rk-bk-teams-klassengrenzen-vaststellen/'  # comp_pk

    real_testfile_pdf_25m1pijl = 'CompLaagBond/test-files/test_bk-25m1pijl-teams_pdf.pdf'
    real_testfile_indoor_f8 = 'CompLaagBond/test-files/test_bk-indoor-teams_f8.xlsx'
    real_testfile_indoor_f4_1234 = 'CompLaagBond/test-files/test_bk-indoor-teams_f4_1234.xlsx'
    real_testfile_indoor_f4_2143 = 'CompLaagBond/test-files/test_bk-indoor-teams_f4_2143.xlsx'
    real_testfile_25m1pijl = 'CompLaagBond/test-files/test_bk-25m1pijl-teams.xlsx'

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
            # print('ver:', ver_nr)
            data.maak_rk_deelnemers(25, ver_nr, cls.regio_nr)

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

        for ver_nr in cls.testdata.regio_ver_nrs[cls.regio_nr][:2]:
            # print('ver:', ver_nr)
            data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

            per_team = 3 if ver_nr == 4092 else 4
            data.maak_rk_teams(18, ver_nr, per_team, limit_teamtypen=['C'])
        # for

    def setUp(self):
        self.e2e_login_and_pass_otp(self.testdata.account_bb)

        # prep Indoor
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')
        zet_competitie_fase_rk_prep(self.testdata.comp25)      # vereiste vaststellen klassengrenzen
        resp = self.client.post(self.url_vaststellen % self.testdata.comp25.pk)
        self.assert_is_redirect_not_plein(resp)
        self.testdata.maak_bk_teams(25)
        zet_competitie_fase_bk_wedstrijden(self.testdata.comp25)

        # prep 25mp1ijl
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)
        self.e2e_check_rol('BKO')
        zet_competitie_fase_rk_prep(self.testdata.comp18)
        resp = self.client.post(self.url_vaststellen % self.testdata.comp18.pk)
        self.assert_is_redirect_not_plein(resp)
        self.testdata.maak_bk_teams(18)
        zet_competitie_fase_bk_wedstrijden(self.testdata.comp18)

    def test_ianseo_pdf_25m(self):
        # bestand NOK
        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_teams_ianseo-pdf', 'bestand')
        self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_teams_ianseo-pdf',
                                             self.real_testfile_pdf_25m1pijl,
                                             '--verbose')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        #self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())

    def test_indoor(self):
        # bestand NOK
        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_teams', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_teams',
                                             self.real_testfile_indoor_f4_1234,
                                             '--dryrun', '--verbose')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(
            "[ERROR] Kan team 'team-4101-bestaat-niet' van vereniging 4101 op regel 33 niet vinden" in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_teams',
                                             self.real_testfile_indoor_f4_2143,
                                             '--dryrun')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        #self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())

        # zonder dryrun en verbose
        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_teams',
                                             self.real_testfile_indoor_f8,
                                             '--verbose')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        #self.assertTrue('[ERROR] Kan bestand niet vinden' in f1.getvalue())

        # geef een 25m1pijl blad aan de indoor importer
        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_teams',
                                             self.real_testfile_25m1pijl)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue('[WARNING] Geen deelnemende teams, dus geen kampioen' in f2.getvalue())

# end of file
