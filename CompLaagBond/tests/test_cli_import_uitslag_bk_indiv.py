# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.definities import DEELNAME_NEE
from Competitie.models import KampioenschapSporterBoog
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagBondCliImportUitslagBkIndiv(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, import van de BK uitslag """

    real_testfile_ianseo_html_25m1pijl = 'CompLaagBond/test-files/ianseo_html_25m1pijl_indiv.txt'
    real_testfile_ianseo_pdf_25m1pijl = 'CompLaagBond/test-files/ianseo_pdf_25m1pijl_indiv.pdf'

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

        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='25',
                                                         sporterboog__sporter__lid_nr=301842)
        cls.deelnemer_25a = deelnemer

        deelnemer = KampioenschapSporterBoog.objects.get(kampioenschap__competitie__afstand='25',
                                                         sporterboog__sporter__lid_nr=301844)
        cls.deelnemer_25b = deelnemer

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

    def test_ianseo_html_25m(self):
        # bestand NOK
        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html', 'bestand')
        self.assertTrue('[ERROR] Kan het html bestand niet openen' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html',
                                             self.real_testfile_ianseo_html_25m1pijl,
                                             '--dryrun', '--verbose')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-html',
                                             self.real_testfile_ianseo_html_25m1pijl)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

    def test_ianseo_pdf_25m(self):
        # bestand NOK
        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-pdf', 'bestand')
        self.assertTrue('[ERROR] Kan het bestand niet vinden' in f1.getvalue())

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-pdf',
                                             self.real_testfile_ianseo_pdf_25m1pijl,
                                             '--dryrun', '--verbose')
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        # zorg dat een lid uit real_testfile_ianseo_pdf_25m1pijl bestaat
        sporter = self.deelnemer_25a.sporterboog.sporter
        sporter.achternaam = 'Van der V' + 'en'
        sporter.voornaam = 'Jo' + 'ep'
        sporter.save()      # wordt een nieuw record, want lid_nr is PK

        ver = self.testdata.vereniging[self.testdata.ver_nrs[0]]
        ver.ver_nr = 1178       # is ook PK, dus geeft nieuw record
        ver.save()
        self.deelnemer_25b.bij_vereniging = ver
        self.deelnemer_25b.save(update_fields=['bij_vereniging'])
        sporter = self.deelnemer_25b.sporterboog.sporter
        sporter.bij_vereniging = ver
        sporter.voornaam = 'F' + 'rank'
        sporter.achternaam = 'Wijn' + 'en'
        sporter.save()

        f1, f2 = self.run_management_command('import_uitslag_bk_25m1pijl_indiv_ianseo-pdf',
                                             self.real_testfile_ianseo_pdf_25m1pijl)
        # print('f1:', f1.getvalue())
        # print('f2:', f2.getvalue())

        # controleer dat de data aangekomen is
        self.deelnemer_25a.refresh_from_db()
        self.assertEqual(self.deelnemer_25a.result_score_1, 232)
        self.assertEqual(self.deelnemer_25a.result_score_2, 238)


# end of file
