# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Competitie.models import CompetitieMatch
from Competitie.test_utils.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_bk_prep
from CompKampioenschap.operations import MaakTeamsExcel
from Locatie.models import WedstrijdLocatie
from Sporter.models import SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompKampioenschapOpMaakTeamsExcel(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Maak Teams Excel (operations) """

    testdata = None
    team_klasse = None
    ver = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        cls.testdata = data = testdata.TestData()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities(2020)

        ver_nr1, ver_nr2 = list(data.ver_sporters.keys())[:2]
        SporterVoorkeuren.objects.create(sporter=data.ver_sporters[ver_nr1][0])

        cls.ver1 = data.vereniging[ver_nr1]
        cls.ver2 = data.vereniging[ver_nr2]

        cls.loc = WedstrijdLocatie.objects.create(
                                banen_18m=12,
                                banen_25m=12,
                                adres='De Spanning 1, Houtdorp')
        cls.loc.verenigingen.add(cls.ver1)

        data.maak_rk_deelnemers(18, ver_nr1, cls.ver1.regio.regio_nr, limit_boogtypen=('R',))
        data.maak_rk_teams(18, ver_nr1, zet_klasse=True)

        data.maak_rk_deelnemers(18, ver_nr2, cls.ver2.regio.regio_nr, limit_boogtypen=('R',))
        data.maak_rk_teams(18, ver_nr2, zet_klasse=True)

        data.maak_bk_teams(18)

    def setUp(self):
        self.team_klasse = self.testdata.comp18_klassen_rk_bk_teams['R2'][0]

        self.match = CompetitieMatch.objects.create(
                                    competitie=self.testdata.comp18,
                                    beschrijving='test 1',
                                    datum_wanneer='2022-02-22',
                                    tijd_begin_wedstrijd='02:22',
                                    vereniging=self.ver1)
        self.match.refresh_from_db()
        self.match.team_klassen.add(self.team_klasse)

    def test_rk(self):
        zet_competitie_fase_rk_prep(self.testdata.comp18)

        deelkamp = self.testdata.deelkamp18_rk[1]
        deelkamp.matches.add(self.match)

        excel = MaakTeamsExcel(deelkamp, self.team_klasse, self.match)
        resp = excel.vul_excel()
        self.assert200_is_bestand_xlsx(resp)

    def test_bk(self):
        self.match.locatie = self.loc
        self.match.save(update_fields=['locatie'])

        zet_competitie_fase_bk_prep(self.testdata.comp25)

        deelkamp = self.testdata.deelkamp18_bk
        deelkamp.matches.add(self.match)

        excel = MaakTeamsExcel(deelkamp, self.team_klasse, self.match)
        resp = excel.vul_excel()
        self.assert200_is_bestand_xlsx(resp)

    def test_bad(self):
        deelkamp = self.testdata.deelkamp18_bk
        deelkamp.matches.add(self.match)

        with override_settings(INSTALL_PATH='/tmp/does not exist/'):
            excel = MaakTeamsExcel(deelkamp, self.team_klasse, self.match)
            with self.assertRaises(RuntimeError):
                excel.vul_excel()

# end of file
