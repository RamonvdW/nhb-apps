# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType, TeamType
from Competitie.definities import MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN, DEELNAME_NEE
from Competitie.models import (CompetitieMutatie, Competitie, CompetitieIndivKlasse, CompetitieTeamKlasse,
                               CompetitieMatch, Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from CompKampioenschap.operations.maak_mutatie import (aanmaken_wedstrijdformulieren_is_pending,
                                                       maak_mutatie_wedstrijdformulieren_aanmaken)
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from GoogleDrive.models import Bestand
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch


class StorageMock:

    def __init__(self, stdout, begin_jaar: int, share_with_emails: list):
        pass

    @staticmethod
    def check_access():
        return True

    @staticmethod
    def maak_sheet_van_template(afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, rayon_nr: int, fname: str) -> str:
        file_id = '%s %s %s %s %s %s' % (afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname)
        return file_id


class SheetMock:

    def __init__(self, stdout):
        self.file_id = ''

    def selecteer_file(self, file_id: str):
        self.file_id = file_id

    @staticmethod
    def selecteer_sheet(sheet_name: str):
        pass

    def get_range(self, range_a1: str):
        if self.file_id.startswith('rk_'):
            values = [[None, 'cell']]
        else:
            values = [[], [None]]
        return values

    @staticmethod
    def clear_range(range_a1: str):
        pass

    @staticmethod
    def wijzig_cellen(range_a1: str, values: list):
        pass

    @staticmethod
    def stuur_wijzigingen():
        pass

    @staticmethod
    def toon_sheet(sheet_name: str):
        pass

    @staticmethod
    def hide_sheet(sheet_name: str):
        pass


class TestCompKampioenschapMutaties(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Maak Mutaties en Verwerk Mutaties """

    def setUp(self):
        self.comp_18 = Competitie.objects.create(
                                beschrijving='comp_18',
                                afstand='18',
                                begin_jaar=2025)
        self.comp_25 = Competitie.objects.create(
                                beschrijving='comp_25',
                                afstand='25',
                                begin_jaar=2025)

        boog_r = BoogType.objects.get(afkorting='R')

        self.kl_indiv = CompetitieIndivKlasse.objects.create(
                            competitie=self.comp_18,
                            beschrijving='indiv 1',
                            volgorde=1,
                            boogtype=boog_r,
                            min_ag=0,
                            is_ook_voor_rk_bk=True)

        team_r2 = TeamType.objects.create(afkorting='R2')
        team_r2.boog_typen.add(boog_r)

        self.kl_teams= CompetitieTeamKlasse.objects.create(
                            competitie=self.comp_18,
                            volgorde=1,
                            beschrijving='team 1',
                            team_type=team_r2,
                            team_afkorting='BB',
                            min_ag=0,
                            is_voor_teams_rk_bk=True)
        self.kl_teams.boog_typen.add(boog_r)

        match = CompetitieMatch.objects.create(
                        competitie=self.comp_18,
                        beschrijving='test',
                        datum_wanneer='2025-01-01',
                        tijd_begin_wedstrijd='01:23')
        match.indiv_klassen.add(self.kl_indiv)
        match.team_klassen.add(self.kl_teams)

        self.functie_bko = maak_functie('BKO', 'BKO')

        kamp = Kampioenschap.objects.create(
                            deel='BK',
                            competitie=self.comp_18,
                            functie=self.functie_bko)
        kamp.rk_bk_matches.add(match)

        kamp_rk = Kampioenschap.objects.create(
                            deel='RK',
                            competitie=self.comp_18,
                            functie=self.functie_bko)
        kamp_rk.rk_bk_matches.add(match)

        regio_106 = Regio.objects.get(regio_nr=106)

        ver = Vereniging.objects.create(
                        ver_nr=1001,
                        naam='Grote club',
                        plaats='',
                        regio=regio_106)

        sporter = Sporter.objects.create(
                            lid_nr=100001,
                            voornaam='Tien',
                            achternaam='Scoorder',
                            email='tien@test.not',
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
                                boogtype=boog_r,
                                voor_wedstrijd=True)

        deelnemer_1 = KampioenschapSporterBoog.objects.create(
                                kampioenschap=kamp_rk,
                                sporterboog=sporterboog,
                                bij_vereniging=sporter.bij_vereniging,
                                indiv_klasse=self.kl_indiv,
                                volgorde=1,
                                rank=1,
                                gemiddelde=9,
                                deelname=DEELNAME_NEE)

        # nog een deelnemer, met para voorkeuren
        sporter = Sporter.objects.create(
                            lid_nr=100002,
                            voornaam='Elf',
                            achternaam='Scoorder',
                            email='elf@test.not',
                            geboorte_datum='1999-09-09',
                            geslacht='M',
                            sinds_datum='2019-01-01',
                            lid_tot_einde_jaar=2025,
                            bij_vereniging=ver)

        SporterVoorkeuren.objects.create(
                            sporter=sporter,
                            para_voorwerpen=True,
                            opmerking_para_sporter='test')

        sporterboog = SporterBoog.objects.create(
                                sporter=sporter,
                                boogtype=boog_r,
                                voor_wedstrijd=True)

        deelnemer_2 = KampioenschapSporterBoog.objects.create(
                                kampioenschap=kamp_rk,
                                sporterboog=sporterboog,
                                bij_vereniging=sporter.bij_vereniging,
                                indiv_klasse=self.kl_indiv,
                                volgorde=1,
                                rank=1,
                                gemiddelde=9)

        # nog een deelnemer, met para voorkeuren
        sporter = Sporter.objects.create(
                            lid_nr=100003,
                            voornaam='Twaalf',
                            achternaam='Scoorder',
                            email='twaalf@test.not',
                            geboorte_datum='1999-09-09',
                            geslacht='V',
                            sinds_datum='2019-01-01',
                            lid_tot_einde_jaar=2025,
                            bij_vereniging=ver)

        SporterVoorkeuren.objects.create(
                            sporter=sporter,
                            para_voorwerpen=False,
                            opmerking_para_sporter='test')

        sporterboog = SporterBoog.objects.create(
                                sporter=sporter,
                                boogtype=boog_r,
                                voor_wedstrijd=True)

        deelnemer_3 = KampioenschapSporterBoog.objects.create(
                                kampioenschap=kamp_rk,
                                sporterboog=sporterboog,
                                bij_vereniging=sporter.bij_vereniging,
                                indiv_klasse=self.kl_indiv,
                                volgorde=1,
                                rank=1,
                                gemiddelde=9)

        team = KampioenschapTeam.objects.create(
                            kampioenschap=kamp,
                            vereniging=ver,
                            volg_nr=1,
                            team_type=team_r2,
                            team_naam='test',
                            aanvangsgemiddelde=15,
                            volgorde=1,
                            rank=1,
                            team_klasse=self.kl_teams)
        team.gekoppelde_leden.add(deelnemer_1)
        team.gekoppelde_leden.add(deelnemer_2)
        team.gekoppelde_leden.add(deelnemer_3)

        team = KampioenschapTeam.objects.create(
                            kampioenschap=kamp,
                            vereniging=ver,
                            volg_nr=2,
                            team_type=team_r2,
                            team_naam='test',
                            aanvangsgemiddelde=10,
                            volgorde=2,
                            rank=2,
                            team_klasse=self.kl_teams)

        team = KampioenschapTeam.objects.create(
                            kampioenschap=kamp,
                            vereniging=ver,
                            volg_nr=3,
                            team_type=team_r2,
                            team_naam='test',
                            aanvangsgemiddelde=5,
                            volgorde=3,
                            rank=3,
                            team_klasse=self.kl_teams)

    def test_wf_aanmaken(self):
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        self.assertFalse(aanmaken_wedstrijdformulieren_is_pending())

        maak_mutatie_wedstrijdformulieren_aanmaken(self.comp_18, door="test")
        self.assertEqual(CompetitieMutatie.objects.count(), 1)

        self.assertTrue(aanmaken_wedstrijdformulieren_is_pending())

        _, f2, = self.verwerk_competitie_mutaties(ignore_errors=True)
        self.assertTrue('[INFO] Maak wedstrijdformulieren voor comp_18' in f2.getvalue())
        self.assertTrue('[ERROR] StorageError: No token' in f2.getvalue())

        # hergebruik de mutatie
        mutatie = CompetitieMutatie.objects.first()
        mutatie.is_verwerkt = False
        mutatie.save(update_fields=['is_verwerkt'])

        with patch('CompKampioenschap.operations.verwerk_mutaties.time.sleep', return_value=None):
            with patch('CompKampioenschap.operations.verwerk_mutaties.StorageWedstrijdformulieren', new=StorageMock):
                _, f2, = self.verwerk_competitie_mutaties()
                self.assertTrue("""[INFO] Maak rk-programma_individueel-rayon1_indiv-1
[INFO] Maak rk-programma_individueel-rayon2_indiv-1
[INFO] Maak rk-programma_individueel-rayon3_indiv-1
[INFO] Maak rk-programma_individueel-rayon4_indiv-1
[INFO] Maak bk-programma_individueel_indiv-1""" in f2.getvalue())
            # teams is uitgezet
            # [INFO] Maak rk-programma_teams-rayon1_team-1
            # [INFO] Maak rk-programma_teams-rayon2_team-1
            # [INFO] Maak rk-programma_teams-rayon3_team-1
            # [INFO] Maak rk-programma_teams-rayon4_team-1
            # [INFO] Maak bk-programma_teams_team-1

    def test_update_dirty_18(self):
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        Bestand.objects.create(
                        begin_jaar=self.comp_18.begin_jaar,
                        afstand=18,
                        is_teams=False,
                        is_bk=True,
                        klasse_pk=123,      # no match
                        is_dirty=True,
                        fname='dirty123',
                        file_id='file123')

        Bestand.objects.create(
                        begin_jaar=self.comp_18.begin_jaar,
                        afstand=18,
                        is_teams=False,
                        is_bk=True,
                        klasse_pk=self.kl_indiv.pk,
                        is_dirty=True,
                        fname='bk_indiv_1',
                        file_id='bk_indiv')

        Bestand.objects.create(
                        begin_jaar=self.comp_18.begin_jaar,
                        afstand=18,
                        is_teams=False,
                        is_bk=False,
                        klasse_pk=self.kl_indiv.pk,
                        is_dirty=True,
                        fname='rk_indiv_1',
                        file_id='rk_indiv')

        Bestand.objects.create(
                        begin_jaar=self.comp_18.begin_jaar,
                        afstand=18,
                        is_teams=True,
                        is_bk=True,
                        klasse_pk=self.kl_teams.pk,
                        is_dirty=True,
                        fname='bk_teams_1',
                        file_id='bk_teams')

        Bestand.objects.create(
                        begin_jaar=self.comp_18.begin_jaar,
                        afstand=18,
                        is_teams=True,
                        is_bk=False,
                        klasse_pk=self.kl_teams.pk,
                        is_dirty=True,
                        fname='rk_teams_1',
                        file_id='rk_teams')

        CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN,
                            competitie=self.comp_18)      # alleen nodig voor begin_jaar

        # geen match op bestand.klasse_pk
        with patch('CompKampioenschap.operations.verwerk_mutaties.time.sleep', return_value=None):
            with patch('CompKampioenschap.operations.verwerk_mutaties.StorageGoogleSheet', new=SheetMock):
                _, f2, = self.verwerk_competitie_mutaties()

    def test_update_dirty_25(self):
        self.assertEqual(CompetitieMutatie.objects.count(), 0)

        Bestand.objects.create(
                        begin_jaar=self.comp_25.begin_jaar,
                        afstand=25,
                        is_teams=False,
                        is_bk=True,
                        klasse_pk=self.kl_indiv.pk,
                        is_dirty=True,
                        fname='bk_indiv_1',
                        file_id='bk_indiv')

        Bestand.objects.create(
                        begin_jaar=self.comp_25.begin_jaar,
                        afstand=25,
                        is_teams=True,
                        is_bk=True,
                        klasse_pk=self.kl_teams.pk,
                        is_dirty=True,
                        fname='bk_teams_1',
                        file_id='bk_teams')

        CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN,
                            competitie=self.comp_25)      # alleen nodig voor begin_jaar

        with patch('CompKampioenschap.operations.verwerk_mutaties.time.sleep', return_value=None):
            with patch('CompKampioenschap.operations.verwerk_mutaties.StorageGoogleSheet', new=SheetMock):
                _, f2, = self.verwerk_competitie_mutaties()


# end of file
