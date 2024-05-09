# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.operations.overstappen import competitie_hanteer_overstap_sporter
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_prep
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import io


class TestCompetitieOperationsOverstappen(E2EHelpers, TestCase):

    """ tests voor de Competitie applicatie, operations Overstappen """

    test_after = ('BasisTypen', 'Functie', 'Competitie.tests.test_tijdlijn')

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        regio_nr = 111
        data.maak_rk_deelnemers(25, data.regio_ver_nrs[regio_nr][0], regio_nr)

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """

        ver_nr = self.testdata.regio_ver_nrs[112][0]        # zelfde rayon
        self.deelnemer1 = self.testdata.comp25_rk_deelnemers[0]
        self.deelnemer1.bij_vereniging = self.testdata.vereniging[ver_nr]
        self.deelnemer1.save(update_fields=['bij_vereniging'])

        ver_nr = self.testdata.regio_ver_nrs[101][0]        # ander rayon
        self.deelnemer2 = self.testdata.comp25_rk_deelnemers[1]
        self.deelnemer2.bij_vereniging = self.testdata.vereniging[ver_nr]
        self.deelnemer2.save(update_fields=['bij_vereniging'])

        deelkamp_bk = self.testdata.deelkamp25_bk
        ver_nr = self.testdata.regio_ver_nrs[101][0]        # ander rayon
        self.deelnemer3 = self.testdata.comp25_rk_deelnemers[2]
        self.deelnemer3.kampioenschap = deelkamp_bk
        self.deelnemer3.bij_vereniging = self.testdata.vereniging[ver_nr]
        self.deelnemer3.save(update_fields=['kampioenschap', 'bij_vereniging'])

    def test_overstappen_regio(self):
        # verkeerde fase
        stdout = io.StringIO()
        competitie_hanteer_overstap_sporter(stdout)
        self.assertFalse('geaccepteerd voor' in stdout.getvalue())

    def test_overstappen_rk(self):
        # zet de competitie in de RK fase
        zet_competitie_fase_rk_prep(self.testdata.comp25)

        stdout = io.StringIO()
        competitie_hanteer_overstap_sporter(stdout)
        self.assertTrue('geaccepteerd voor' in stdout.getvalue())

    def test_overstappen_bk(self):
        # zet de competitie in de BK fase
        zet_competitie_fase_bk_prep(self.testdata.comp25)

        stdout = io.StringIO()
        competitie_hanteer_overstap_sporter(stdout)
        # print('stdout: %s' % stdout.getvalue())
        self.assertTrue('geaccepteerd voor' in stdout.getvalue())

# end of file
