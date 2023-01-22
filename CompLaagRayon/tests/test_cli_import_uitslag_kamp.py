# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import KampioenschapSporterBoog, DEELNAME_NEE
from Competitie.tests.test_fase import zet_competitie_fase
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonCliImportUitslagKamp(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK uitslag """

    real_testfile_25m1pijl = 'CompLaagRayon/management/testfiles/test_rk-25m1p_indiv.xlsm'
    real_testfile_indoor = 'CompLaagRayon/management/testfiles/test_rk-indoor_indiv.xlsm'

    testdata = None
    rayon_nr = 3
    regio_nr = 101 + (rayon_nr - 1) * 4

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()
        cls.testdata.maak_clubs_en_sporters()
        cls.testdata.maak_bondscompetities()

        ver_nr = cls.testdata.regio_ver_nrs[cls.regio_nr][0]
        cls.testdata.maak_rk_deelnemers(25, ver_nr, cls.regio_nr)
        cls.testdata.maak_rk_deelnemers(18, ver_nr, cls.regio_nr)

        # meld een paar deelnemers af
        for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand='25',
                                                                 sporterboog__sporter__lid_nr__in=(301946, 301976)):
            deelnemer.deelname = DEELNAME_NEE
            deelnemer.save(update_fields=['deelname'])
        # for

        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                         sporterboog__sporter__lid_nr=301946,
                                                         indiv_klasse__boogtype__afkorting='C')
        deelnemer.deelname = DEELNAME_NEE
        deelnemer.save(update_fields=['deelname'])

        # geef een sporter alvast een rank
        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                         sporterboog__sporter__lid_nr=301951)
        deelnemer.result_rank = 5;
        deelnemer.save(update_fields=['result_rank'])

        ver_nr = cls.testdata.regio_ver_nrs[116][0]
        cls.testdata.maak_rk_deelnemers(25, ver_nr, 101)                # ander rayon

        # zet de competities in fase L
        zet_competitie_fase(cls.testdata.comp18, 'L')
        zet_competitie_fase(cls.testdata.comp25, 'L')

        # prev_klasse = None
        # for deelnemer in KampioenschapSporterBoog.objects.filter(kampioenschap__competitie__afstand=18).prefetch_related('indiv_klasse').order_by('indiv_klasse__volgorde'):
        #     if deelnemer.indiv_klasse.pk != prev_klasse:
        #         print('---', deelnemer.indiv_klasse)
        #         prev_klasse = deelnemer.indiv_klasse.pk
        #     print(deelnemer, deelnemer.gemiddelde)
        # # for

    def setUp(self):
        pass

    def test_25m(self):
        # file NOK
        self.run_management_command('import_uitslag_kamp_25m1pijl', 'bestand', 'blad', 'A', 'B', 'C')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen')

        # blad NOK
        f1, f2 = self.run_management_command('import_uitslag_kamp_25m1pijl', self.real_testfile_25m1pijl, 'blad', 'A', 'B', 'C')
        self.assertTrue("[ERROR] Kan blad 'blad' niet vinden" in f1.getvalue())

        # kolommen NOK
        f1, f2 = self.run_management_command('import_uitslag_kamp_25m1pijl', self.real_testfile_25m1pijl, 'Wedstrijd', 'A', 'B', 'C')
        self.assertTrue('[ERROR] Vereiste kolommen: ' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_kamp_25m1pijl', self.real_testfile_25m1pijl, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O', '--dryrun')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] Kan deelnemer niet bepalen voor regel 7' in f1.getvalue())
        self.assertTrue('[ERROR] Score is niet aflopend op regel 11' in f1.getvalue())
        self.assertTrue('[ERROR] Probleem met 10/9/8 count op regel 13' in f1.getvalue())
        self.assertTrue('[ERROR] Probleem met scores op regel 16' in f1.getvalue())
        self.assertTrue('[ERROR] Geen RK deelnemer op regel 17: 123456' in f1.getvalue())
        self.assertTrue('[WARNING] Regel 14 wordt overgeslagen (geen scores)' in f2.getvalue())

        # echte import
        self.run_management_command('import_uitslag_kamp_25m1pijl', self.real_testfile_25m1pijl, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O')

        # geef de dupe-check iets om op te reageren
        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand=25,
                                                         sporterboog__sporter__lid_nr=301966)
        deelnemer.result_counts = 'test'
        deelnemer.save(update_fields=['result_counts'])

        # tweede import zodat dupe check gedaan wordt
        f1, f2 = self.run_management_command('import_uitslag_kamp_25m1pijl', self.real_testfile_25m1pijl, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue(' heeft al andere resultaten!' in f1.getvalue())
        self.assertTrue(' [301966] ' in f1.getvalue())

    def test_18m(self):
        # file NOK
        self.run_management_command('import_uitslag_kamp_indoor', 'bestand', 'blad', 'A', 'B', 'C')
        self.assertTrue('[ERROR] Kan het excel bestand niet openen')

        # blad NOK
        f1, f2 = self.run_management_command('import_uitslag_kamp_indoor', self.real_testfile_25m1pijl, 'blad', 'A', 'B', 'C')
        self.assertTrue("[ERROR] Kan blad 'blad' niet vinden" in f1.getvalue())

        # kolommen NOK
        f1, f2 = self.run_management_command('import_uitslag_kamp_indoor', self.real_testfile_25m1pijl, 'Wedstrijd', 'A', 'B', 'C')
        self.assertTrue('[ERROR] Vereiste kolommen: ' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_kamp_indoor', self.real_testfile_indoor, 'Voorronde', 'D', 'J', 'K', 'Q', '--dryrun')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('(Recurve) hoort in klasse: Recurve Onder 21 klasse 2' in f1.getvalue())
        self.assertTrue('[ERROR] Geen RK deelnemer op regel 23: 123456' in f1.getvalue())
        self.assertTrue("[ERROR] Probleem met scores op regel 25: 'n/a' en 'n/a'" in f1.getvalue())
        self.assertTrue("[INFO] Klasse: Recurve klasse 6" in f2.getvalue())
        self.assertTrue("1: RK rayon 3 [301954]" in f2.getvalue())
        self.assertTrue("[WARNING] Regel 24 wordt overgeslagen (geen scores)" in f2.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_kamp_indoor', self.real_testfile_indoor, 'Voorronde', 'D', 'J', 'K', 'Q')
        _ = (f1, f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        kampioen = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='18',
                                                        sporterboog__sporter__lid_nr=301954)
        self.assertEqual(kampioen.result_rank, 1)
        self.assertEqual(kampioen.result_score_1, 204)
        self.assertEqual(kampioen.result_score_2, 228)
        self.assertEqual(kampioen.result_counts, '')        # alleen voor 25m1pijl


# end of file
