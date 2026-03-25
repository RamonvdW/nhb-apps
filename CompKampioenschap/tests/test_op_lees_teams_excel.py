# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from CompKampioenschap.operations import LeesTeamsExcel
from CompLaagRayon.models import KampRK, DeelnemerRK, TeamRK
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
from types import SimpleNamespace


class TestCompKampioenschapOpLeesTeamsExcel(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Importeer Uitslag Indiv (google sheets) """

    def _maak_rk_deelnemer(self, lid_nr, ver, voornaam, achternaam):
        sporter = Sporter.objects.create(
                            lid_nr=lid_nr,
                            voornaam=voornaam,
                            achternaam=achternaam,
                            email='',
                            geboorte_datum='1999-09-09',
                            geslacht='M',
                            sinds_datum='2019-01-01',
                            lid_tot_einde_jaar=2025,
                            bij_vereniging=ver)

        # geen para
        SporterVoorkeuren.objects.create(
                            sporter=sporter,
                            para_voorwerpen=False,
                            opmerking_para_sporter='')

        sporterboog = SporterBoog.objects.create(
                                sporter=sporter,
                                boogtype=self.boog_r,
                                voor_wedstrijd=True)

        deelnemer = DeelnemerRK.objects.create(
                                kamp=self.kamp_rk,
                                sporterboog=sporterboog,
                                indiv_klasse=self.indiv_klasse,
                                indiv_klasse_volgende_ronde=self.indiv_klasse,
                                bij_vereniging=ver,
                                bevestiging_gevraagd_op='2000-01-01T00:00:00Z',
                                gemiddelde=10.0)

        return deelnemer

    def _maak_rk_team(self, ver: Vereniging, deelnemers: list[DeelnemerRK]) -> TeamRK:

        ag_som = sum([deelnemer.gemiddelde for deelnemer in deelnemers])

        team = TeamRK.objects.create(
                        kamp=self.kamp_rk,
                        vereniging=ver,
                        volg_nr=1,
                        team_type=self.team_r,
                        team_klasse=self.team_klasse,
                        team_klasse_volgende_ronde=self.team_klasse,
                        team_naam='Team %s-1' % ver.ver_nr,
                        #deelname=DEELNAME_ONBEKEND
                        is_reserve=False,
                        aanvangsgemiddelde=ag_som,
                        volgorde=1,
                        rank=1)
        team.gekoppelde_leden.set(deelnemers)

        return team

    def setUp(self):
        self.vers = list()
        for lp in (1, 2, 3, 4):
            self.vers.append(
                    Vereniging.objects.create(
                                        ver_nr=1000 + lp,
                                        naam='Ver %s' % lp,
                                        regio=Regio.objects.get(regio_nr=108+lp),
                                        plaats='')
            )
        # for

        self.comp = Competitie.objects.create(
                            begin_jaar=2025,
                            beschrijving='Comp18',
                            afstand='18')
        self.comp.refresh_from_db()

        self.rayon3 = Rayon.objects.get(rayon_nr=3)

        self.functie_rko = maak_functie('RKO Rayon 3', 'RKO')
        self.functie_rko.rayon = self.rayon3
        self.functie_rko.save(update_fields=['rayon'])

        self.kamp_rk = KampRK.objects.create(
                            competitie=self.comp,
                            functie=self.functie_rko,
                            rayon=self.rayon3,
                            heeft_deelnemerslijst=True)

        self.boog_r = BoogType.objects.get(afkorting='R')
        self.team_r = TeamType.objects.get(afkorting='R2')

        self.indiv_klasse = CompetitieIndivKlasse.objects.create(
                                    competitie=self.comp,
                                    boogtype=self.boog_r,
                                    is_ook_voor_rk_bk=True,
                                    volgorde=1,
                                    beschrijving='test',
                                    min_ag=0)

        self.team_klasse = CompetitieTeamKlasse.objects.create(
                                    competitie=self.comp,
                                    volgorde=1,
                                    beschrijving='R kl A',
                                    team_type=self.team_r,
                                    team_afkorting='R2',
                                    min_ag=0,
                                    is_voor_teams_rk_bk=True,
                                    krijgt_scheids_rk=True,
                                    krijgt_scheids_bk=True)
        self.team_klasse.boog_typen.add(self.boog_r)

        self.deelnemers = list()
        self.teams = list()

        lid_nr = 100000
        for ver in self.vers:
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 1, ver, 'Een', 'Teamlid'))
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 2, ver, 'Twee', 'Teamlid'))
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 3, ver, 'Drie', 'Teamlid'))
            lid_nr += 100

            self.teams.append(self._maak_rk_team(ver, self.deelnemers[-3:]))
        # for

    def _make_sheet(self, cells):
        sheet = dict()
        for range_a1, value in cells.items():
            sheet[range_a1] = SimpleNamespace(value=value)
        # for
        return sheet

    def test_exception(self):
        class MockLoadException:
            def load_workbook(self, *args, **kwargs):
                raise OSError('test')

        with patch('CompKampioenschap.operations.lees_teams_excel.openpyxl', new=MockLoadException):
            lees = LeesTeamsExcel()
            lees.lees_bestand('fname.xlsx')
            self.assertTrue('[ERROR] Kan het excel bestand niet openen (test)' in lees.issues)


    def test_1(self):
        sheet_deelnemers = self._make_sheet({
            'B8': 'Team 1',
            'C8': '1001',
            'C9': str(self.deelnemers[0].sporterboog.sporter.lid_nr),
            'C10': str(self.deelnemers[1].sporterboog.sporter.lid_nr),
            'C11': self.deelnemers[2].sporterboog.sporter.lid_nr,
            'D9': str(self.deelnemers[0].gemiddelde),
            'D10': str(self.deelnemers[1].gemiddelde),
            'D11': str(self.deelnemers[2].gemiddelde),

            'B13': 'Team 2',
            'C13': '1002',
            'C14': self.deelnemers[3].sporterboog.sporter.lid_nr,
            'C15': self.deelnemers[4].sporterboog.sporter.lid_nr,
            'C16': self.deelnemers[5].sporterboog.sporter.lid_nr,
            'D14': str(self.deelnemers[3].gemiddelde),
            'D15': str(self.deelnemers[4].gemiddelde),
            'D16': str(self.deelnemers[5].gemiddelde),

            'B18': 'Team 3',
            'C18': '1003',
            'C19': self.deelnemers[6].sporterboog.sporter.lid_nr,
            'C20': self.deelnemers[7].sporterboog.sporter.lid_nr,
            'C21': self.deelnemers[8].sporterboog.sporter.lid_nr,
            'D19': str(self.deelnemers[6].gemiddelde),
            'D20': str(self.deelnemers[7].gemiddelde),
            'D21': str(self.deelnemers[8].gemiddelde),

            # error handling:
            'B23': 'Bad',
            'C23': 'ver_nr',

            'B28': None,
            'B33': 'N.V.T.',
            'B38': 'nvt',

            'B43': 'Team 8',
            'C43': '0',
            'C44': 'bad',
            'C45': '0',
            'D45': '10...0',
            'C46': None
        })
        sheet_stand = self._make_sheet({
            'C8': 'Team 1',         # team naam
            'E8': '20',             # matchpunten
            'F8': None,             # shootoff

            'C9': 'Team 2',
            'E9': '18',
            'F9': '27',

            'C10': 'Team 3',
            'E10': '18',
            'F10': '26',

            'C11': 'Fout',
            'E11': 'x10',

            'C12': 'Fout',
            'E12': '10',
            'F12': 'x10',

            'C13': '',
            'C14': '',
            'C15': '',
        })
        prg = {
            'Stand': sheet_stand,
            'Deelnemers': sheet_deelnemers,
        }
        with patch('CompKampioenschap.operations.lees_teams_excel.openpyxl.load_workbook', return_value=prg):
            lees = LeesTeamsExcel()
            lees.lees_bestand('fname.xlsx')

            # for regel in lees.issues:
            #     print(regel)
            self.assertEqual(len(lees.issues), 4)
            self.assertTrue("[ERROR] Geen valide lid_nr 'bad' op regel 44" in lees.issues)
            self.assertTrue("[ERROR] Geen valide AG '10...0' op regel 45" in lees.issues)
            self.assertTrue("[ERROR] Geen valide matchpunten 'x10' op regel 11" in lees.issues)
            self.assertTrue("[ERROR] Geen valide shootoff 'x10' op regel 12" in lees.issues)

            # print(lees.teams)
            self.assertEqual(len(lees.teams), 4)
            self.assertEqual(lees.teams[0].ver_nr, 1001)
            self.assertEqual(lees.teams[1].ver_nr, 1002)
            self.assertEqual(lees.teams[2].ver_nr, 1003)
            self.assertEqual(lees.teams[3].ver_nr, 0)
            self.assertEqual(len(lees.teams[0].leden), 3)
            self.assertEqual(len(lees.teams[1].leden), 3)
            self.assertEqual(len(lees.teams[2].leden), 3)
            self.assertEqual(len(lees.teams[3].leden), 0)

            # print(lees.eindstand)
            self.assertEqual(len(lees.eindstand), 3)
            self.assertEqual(lees.eindstand[0].matchpunten, 20)
            self.assertIsNone(lees.eindstand[0].shootoff)
            self.assertEqual(lees.eindstand[1].matchpunten, 18)
            self.assertEqual(lees.eindstand[1].shootoff, 27)
            self.assertEqual(lees.eindstand[2].matchpunten, 18)
            self.assertEqual(lees.eindstand[2].shootoff, 26)

# end of file
