# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEELNAME_NEE
from Competitie.models import KampioenschapSporterBoog
from Competitie.tijdlijn import zet_competitie_fase_bk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagBondCliImportUitslagBkIndiv(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, import van de BK uitslag """

    # real_testfile_25m1pijl = 'CompLaagBond/management/testfiles/test_bk-25m1pijl-indiv.xlsx'
    real_testfile_indoor = 'CompLaagBond/management/testfiles/test_bk-indoor-indiv.xlsx'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][0]
        data.maak_rk_deelnemers(25, ver_nr, cls.regio_nr)
        data.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

        # meld een paar deelnemers af
        for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand='25',
                                                                 sporterboog__sporter__lid_nr__in=(301826, 301831)):
            deelnemer.deelname = DEELNAME_NEE
            deelnemer.save(update_fields=['deelname'])
        # for

        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                         sporterboog__sporter__lid_nr=301826,
                                                         indiv_klasse__boogtype__afkorting='C')
        deelnemer.deelname = DEELNAME_NEE
        deelnemer.save(update_fields=['deelname'])

        # geef een sporter alvast een rank
        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                         sporterboog__sporter__lid_nr=301842)
        deelnemer.result_rank = 5
        deelnemer.save(update_fields=['result_rank'])

        # verander de RK deelnemers in BK deelnemers
        for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand='18'):
            deelnemer.kampioenschap = data.deelkamp18_bk
            deelnemer.save(update_fields=['kampioenschap'])
        # for

        for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand='25'):
            deelnemer.kampioenschap = data.deelkamp25_bk
            deelnemer.save(update_fields=['kampioenschap'])
        # for

        # zet de competities in fase P
        zet_competitie_fase_bk_wedstrijden(data.comp18)
        zet_competitie_fase_bk_wedstrijden(data.comp25)

    def setUp(self):
        pass

    # def test_25m(self):
    #     # bestand NOK
    #     self.run_management_command('import_uitslag_rk_25m1pijl_indiv', 'bestand')
    #     self.assertTrue('[ERROR] Kan het excel bestand niet openen')
    #
    #     f1, f2 = self.run_management_command('import_uitslag_rk_25m1pijl_indiv', self.real_testfile_25m1pijl, '--dryrun')
    #     # print('\nf1: %s' % f1.getvalue())
    #     # print('\nf2: %s' % f2.getvalue())
    #     self.assertTrue('[ERROR] Kan deelnemer niet bepalen voor regel 7' in f1.getvalue())
    #     self.assertTrue('[ERROR] Score is niet aflopend op regel 11' in f1.getvalue())
    #     # self.assertTrue('[ERROR] Probleem met 10/9/8 count op regel 13' in f1.getvalue())
    #     self.assertTrue('[ERROR] Probleem met scores op regel 16' in f1.getvalue())
    #     self.assertTrue('[ERROR] Geen RK deelnemer op regel 17: 123456' in f1.getvalue())
    #     self.assertTrue('[WARNING] Regel 14 wordt overgeslagen (geen scores)' in f2.getvalue())
    #
    #     # echte import
    #     self.run_management_command('import_uitslag_rk_25m1pijl_indiv', self.real_testfile_25m1pijl)
    #
    #     # geef de dupe-check iets om op te reageren
    #     deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand=25,
    #                                                      sporterboog__sporter__lid_nr=301834)
    #     deelnemer.result_counts = 'test'
    #     deelnemer.save(update_fields=['result_counts'])
    #
    #     # tweede import zodat dupe check gedaan wordt
    #     f1, f2 = self.run_management_command('import_uitslag_rk_25m1pijl_indiv', self.real_testfile_25m1pijl)
    #     # print('\nf1: %s' % f1.getvalue())
    #     # print('\nf2: %s' % f2.getvalue())
    #     self.assertTrue(' heeft al andere resultaten!' in f1.getvalue())
    #     self.assertTrue('[301834] ' in f1.getvalue())

    def test_18m(self):
        # file NOK
        self.run_management_command('import_uitslag_bk_indoor_indiv', 'bestand')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen')

        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_indiv', self.real_testfile_indoor, '--dryrun', '--verbose')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('hoort in klasse: Longbow klasse 2' in f1.getvalue())
        self.assertTrue('[ERROR] Geen BK deelnemer op regel 25: 123456' in f1.getvalue())
        self.assertTrue("[ERROR] Probleem met scores op regel 27: 'n/a' en 'n/a'" in f1.getvalue())
        self.assertTrue("[INFO] Klasse: Recurve klasse 6" in f2.getvalue())
        self.assertTrue("[WARNING] Regel 26 wordt overgeslagen (geen scores)" in f2.getvalue())
        self.assertTrue("Volgorde=1, Rank=1, Q-scores=204, 228, deelnemer=[301849]" in f2.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_indoor_indiv', self.real_testfile_indoor)
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        kampioen = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                        sporterboog__sporter__lid_nr=301849)
        self.assertEqual(kampioen.result_rank, 1)
        self.assertEqual(kampioen.result_score_1, 204)
        self.assertEqual(kampioen.result_score_2, 228)
        self.assertEqual(kampioen.result_counts, '')        # alleen voor 25m1pijl


# end of file
