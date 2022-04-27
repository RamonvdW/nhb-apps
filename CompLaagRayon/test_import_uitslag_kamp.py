# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Competitie.test_fase import zet_competitie_fase
from Competitie.models import KampioenschapSchutterBoog, DEELNAME_NEE
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import io


class TestCompRayonImportUitslagKampioenschap(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, import van de RK/BK uitslag """

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
        for deelnemer in KampioenschapSchutterBoog.objects.filter(sporterboog__sporter__lid_nr__in=(301946, 301976)):
            deelnemer.deelname = DEELNAME_NEE
            deelnemer.save(update_fields=['deelname'])

        ver_nr = cls.testdata.regio_ver_nrs[116][0]
        cls.testdata.maak_rk_deelnemers(25, ver_nr, 101)                # ander rayon

        # zet de competities in fase L
        zet_competitie_fase(cls.testdata.comp18, 'L')
        zet_competitie_fase(cls.testdata.comp25, 'L')

    def setUp(self):
        pass

    def test_25m_indiv(self):
        real_file = 'CompLaagRayon/management/testfiles/test_rk-programma_individueel-rayon2_compound-klasse-2.xlsm'

        # afstand NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('import_uitslag_kamp', '999', 'bestand', 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Afstand moet 18 of 25 zijn')

        # file NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', 'bestand', 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Kan het excel bestand niet openen')

        # blad NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', real_file, 'blad', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue("[ERROR] Kan blad 'blad' niet vinden" in f1.getvalue())

        # kolommen NOK
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', real_file, 'Wedstrijd', 'A', 'B', 'C', stderr=f1, stdout=f2)
        self.assertTrue('[ERROR] Vereiste kolommen: ' in f1.getvalue())

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', real_file, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O', '--dryrun', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] Kan deelnemer niet bepalen voor regel 7' in f1.getvalue())
        self.assertTrue('[ERROR] Score is niet aflopend op regel 11' in f1.getvalue())
        self.assertTrue('[ERROR] Probleem met 10/9/8 count op regel 13' in f1.getvalue())
        self.assertTrue('[ERROR] Probleem met scores op regel 16' in f1.getvalue())
        self.assertTrue('[ERROR] Geen RK deelnemer op regel 17: 123456' in f1.getvalue())
        self.assertTrue('[WARNING] Regel 14 wordt overgeslagen (geen scores)' in f2.getvalue())

        # echte import
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', real_file, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O', stderr=f1, stdout=f2)

        # geef de dupe-check iets om op te reageren
        deelnemer = KampioenschapSchutterBoog.objects.get(deelcompetitie__competitie__afstand=25,
                                                          sporterboog__sporter__lid_nr=301966)
        deelnemer.result_counts = 'test'
        deelnemer.save(update_fields=['result_counts'])

        # tweede import zodat dupe check gedaan wordt
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '25', real_file, 'Wedstrijd', 'D', 'J', 'K', 'M', 'N', 'O', stderr=f1, stdout=f2)
        print('f1:', f1.getvalue())
        print('f2:', f2.getvalue())
        self.assertTrue(' heeft al andere resultaten!' in f1.getvalue())
        self.assertTrue(' [301966] ' in f1.getvalue())

    def test_18m_indiv(self):
        real_file = 'CompLaagRayon/files/template-excel-rk-indoor-indiv.xlsm'

        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('import_uitslag_kamp', '18', real_file, 'Voorronde', 'A', 'B', 'C', stderr=f1, stdout=f2)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())
        self.assertTrue('[ERROR] Indoor nog niet ondersteund' in f1.getvalue())


# end of file
