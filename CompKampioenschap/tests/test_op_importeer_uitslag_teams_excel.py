# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from BasisTypen.models import BoogType, TeamType
from Competitie.models import Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse
from CompKampioenschap.operations import ImporteerUitslagTeamsExcel
from CompLaagRayon.models import KampRK, DeelnemerRK, TeamRK
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
from types import SimpleNamespace
from decimal import Decimal
import io


class TestCompKampioenschapOpImporteerUitslagTeamsExcel(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Importeer Uitslag Teams Excel """

    def _maak_rk_deelnemer(self, lid_nr, ver, voornaam, achternaam, gemiddelde: int):
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
                                gemiddelde=gemiddelde)

        return deelnemer

    def _maak_rk_team(self, ver: Vereniging, volg_nr, deelnemers: list[DeelnemerRK]) -> TeamRK:

        ag_som = sum([deelnemer.gemiddelde for deelnemer in deelnemers])

        team = TeamRK.objects.create(
                        kamp=self.kamp_rk,
                        vereniging=ver,
                        volg_nr=volg_nr,
                        team_type=self.team_r,
                        team_klasse=self.team_klasse,
                        team_klasse_volgende_ronde=self.team_klasse,
                        team_naam='Team %s-%s' % (ver.ver_nr, volg_nr),
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
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 1, ver, 'Een', 'Teamlid', 8))
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 2, ver, 'Twee', 'Teamlid', 9))
            self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 3, ver, 'Drie', 'Teamlid', 10))
            lid_nr += 100

            self.teams.append(self._maak_rk_team(ver, 1, self.deelnemers[-3:]))
        # for

        ver = self.vers[0]
        lid_nr = 100000
        self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 4, ver, 'Vier', 'Teamlid', 8))
        self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 5, ver, 'Vijf', 'Teamlid', 9))
        self.deelnemers.append(self._maak_rk_deelnemer(lid_nr + 6, ver, 'Zes', 'Teamlid', 10))
        self.teams.append(self._maak_rk_team(ver, 2, self.deelnemers[-3:]))

        # compound team
        boog_c = BoogType.objects.get(afkorting='C')
        team_c = TeamType.objects.get(afkorting='C')
        team_klasse_c = CompetitieTeamKlasse.objects.create(
                                    competitie=self.comp,
                                    volgorde=1,
                                    beschrijving='C kl A',
                                    team_type=team_c,
                                    team_afkorting='C',
                                    min_ag=0,
                                    is_voor_teams_rk_bk=True,
                                    krijgt_scheids_rk=True,
                                    krijgt_scheids_bk=True)
        team_klasse_c.boog_typen.add(boog_c)
        ag_som = Decimal(27.0)
        volg_nr = 9

        team = TeamRK.objects.create(
                        kamp=self.kamp_rk,
                        vereniging=ver,
                        volg_nr=volg_nr,
                        team_type=team_c,
                        team_klasse=team_klasse_c,
                        team_klasse_volgende_ronde=team_klasse_c,
                        team_naam='Team %s-%s' % (ver.ver_nr, volg_nr),
                        #deelname=DEELNAME_ONBEKEND
                        is_reserve=False,
                        aanvangsgemiddelde=ag_som,
                        volgorde=1,
                        rank=1)
        #team.gekoppelde_leden.set(self.deelnemers[-3:])

    def test_fouten(self):
        class MockLeesTeamsExcel1:
            def __init__(self):
                self.issues = ['[ERROR] Inlees fout']
                self.teams = list()
                self.eindstand = list()

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel1):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=True, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

            self.assertTrue('[ERROR] Inlees fout' in stderr.getvalue())

        class MockLeesTeamsExcel2:
            def __init__(self):
                self.issues = list()
                self.teams = list()
                self.eindstand = list()

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel2):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=True, afstand='18', is_bk=True)
            importeer.importeer_bestand('fname.xlsx')

            self.assertTrue('[ERROR] Team klasse niet kunnen bepalen (geen teams)' in stderr.getvalue())

        class MockLeesTeamsExcel3:
            def __init__(self):
                self.issues = list()
                self.teams = [
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001-1',
                        ver_nr=1001,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100001, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100002, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100003, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001-9',  # compound
                        ver_nr=1001,
                        leden=[],
                    ),
                ]
                self.eindstand = list()

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel3):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=True, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

            # print(stdout.getvalue())
            # print(stderr.getvalue())
            self.assertTrue("[ERROR] Kan team klasse niet kiezen uit: [<CompetitieTeamKlasse: R kl A [R2] (0.000) (RK/BK)>, <CompetitieTeamKlasse: C kl A [C] (0.000) (RK/BK)>]" in stderr.getvalue())

        class MockLeesTeamsExcel4:
            def __init__(self):
                self.issues = list()
                self.teams = [
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001',      # Team 1001-1 of 1001-2
                        ver_nr=1001,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100001, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100002, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100003, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Niet herkenbaar',        # Team 1002-1
                        ver_nr=1002,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100101, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100102, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100103, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1003-1 Toppers',        # aangepaste naam
                        ver_nr=1003,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100000, lid_ag=Decimal('8.0')),       # fout: onbekend
                            SimpleNamespace(row_nr=44, lid_nr=100302, lid_ag=Decimal('9.0')),       # fout: ver_nr
                            SimpleNamespace(row_nr=45, lid_nr=100203, lid_ag=Decimal('11.0')),      # fout: ag
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001-2',        # fout
                        ver_nr=1001,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100301, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100302, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100303, lid_ag=Decimal('10.0')),
                        ],
                    ),
                ]
                self.eindstand = list()

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel4):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=True, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

            # print(stdout.getvalue())
            # print(stderr.getvalue())
            self.assertTrue('[INFO] Rayon: 3' in stdout.getvalue())

            self.assertTrue("[ERROR] Lid 100302 is niet van vereniging 1003!" in stderr.getvalue())
            self.assertTrue("[ERROR] Lid 100000 is niet gekwalificeerd voor dit kampioenschap!" in stderr.getvalue())
            self.assertTrue("[ERROR] Maar 1 deelnemers in team 'Team 1003-1" in stderr.getvalue())
            self.assertTrue("[ERROR] Kan team 'Team 1001' van vereniging 1001 op regel 42 niet kiezen uit" in stderr.getvalue())
            self.assertTrue("[ERROR] Kan team 'Team 1001' van vereniging 1001 op regel 42 niet vinden" in stderr.getvalue())
            self.assertTrue("[ERROR] Kan team 'Niet herkenbaar' van vereniging 1002 op regel 42 niet vinden" in stderr.getvalue())

        class MockLeesTeamsExcel5:
            def __init__(self):
                self.issues = list()
                self.teams = [
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001-1',
                        ver_nr=1001,
                        leden=[
                            SimpleNamespace(row_nr=45, lid_nr=100006, lid_ag=Decimal('10.0')),      # vervangt 8.0
                            SimpleNamespace(row_nr=44, lid_nr=100005, lid_ag=Decimal('9.0')),       # vervangt 9.0
                            SimpleNamespace(row_nr=43, lid_nr=100003, lid_ag=Decimal('10.0')),
                        ],
                    ),
                ]
                self.eindstand = list()

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel5):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=False, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

            # print(stdout.getvalue())
            # print(stderr.getvalue())
            self.assertTrue("[ERROR] Te hoog gemiddelde 10.000 voor invaller 100006 voor team Team 1001-1 van vereniging 1001" in stderr.getvalue())

    def test_importeer(self):
        class MockLeesTeamsExcel:
            def __init__(self):
                self.issues = list()
                self.teams = [
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1001-1',
                        ver_nr=1001,
                        leden=[
                            SimpleNamespace(row_nr=45, lid_nr=100001, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100002, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=43, lid_nr=100003, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1002-1',
                        ver_nr=1002,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100101, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100102, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100103, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1003-1',
                        ver_nr=1003,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100201, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100202, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100203, lid_ag=Decimal('10.0')),
                        ],
                    ),
                    SimpleNamespace(
                        row_nr=42,
                        team_naam='Team 1004-1',
                        ver_nr=1004,
                        leden=[
                            SimpleNamespace(row_nr=43, lid_nr=100301, lid_ag=Decimal('8.0')),
                            SimpleNamespace(row_nr=44, lid_nr=100302, lid_ag=Decimal('9.0')),
                            SimpleNamespace(row_nr=45, lid_nr=100303, lid_ag=Decimal('10.0')),
                        ],
                    ),
                ]
                self.eindstand = [
                    SimpleNamespace(team_naam='Team 1001-1', matchpunten=20, shootoff=None),
                    SimpleNamespace(team_naam='Team 1002-1', matchpunten=10, shootoff=25),    # 2e
                    SimpleNamespace(team_naam='Team 1003-1', matchpunten=10, shootoff=25),    # 2e
                    SimpleNamespace(team_naam='Team 1004-1', matchpunten=8, shootoff=None),
                ]

            def lees_bestand(self, _fname):
                pass

        with patch('CompKampioenschap.operations.importeer_uitslag_teams_excel.LeesTeamsExcel', new=MockLeesTeamsExcel):
            stdout = OutputWrapper(io.StringIO())
            stderr = OutputWrapper(io.StringIO())

            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=True, verbose=True, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

            # print(stdout.getvalue())
            # print(stderr.getvalue())
            self.assertTrue("[INFO] Rank 1: 20 punten, shootoff: '', team 'Team 1001-1'" in stdout.getvalue())
            self.assertTrue("[INFO] Rank 2: 10 punten, shootoff: '(SO: 25)', team 'Team 1003-1'" in stdout.getvalue())
            self.assertTrue("[INFO] Rank 2: 10 punten, shootoff: '(SO: 25)', team 'Team 1002-1'" in stdout.getvalue())
            self.assertTrue("[INFO] Rank 4: 8 punten, shootoff: '', team 'Team 1004-1'" in stdout.getvalue())
            self.assertTrue("[WARNING] Team 'Team 1001-2' van ver 1001 staat niet in de uitslag --> no-show" in stdout.getvalue())

            # nog een keer, zonder verbose, zonder dryrun
            importeer = ImporteerUitslagTeamsExcel(stdout, stderr, dryrun=False, verbose=False, afstand='18', is_bk=False)
            importeer.importeer_bestand('fname.xlsx')

# end of file
