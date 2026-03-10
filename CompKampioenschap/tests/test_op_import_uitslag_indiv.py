# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.definities import DEELNAME_ONBEKEND, DEELNAME_JA, DEELNAME_NEE
from Competitie.models import Competitie, CompetitieIndivKlasse
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import importeer_sheet_uitslag_indiv
from CompLaagBond.models import KampBK, DeelnemerBK
from CompLaagRayon.models import KampRK
from Functie.tests.helpers import maak_functie
from Geo.models import Regio, Rayon
from GoogleDrive.models import Bestand
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch
from types import SimpleNamespace


class MockLeesIndivWedstrijdFormulier:

    def __init__(self, stdout, bestand, _sheets, lees_oppervlakkig: bool):
        self.stdout = stdout
        self.afstand = bestand.afstand
        self.lees_oppervlakkig = lees_oppervlakkig
        self._params = bestand.params
        self.finales_blad = self._params.finales_blad

        for regel in self._params.foutmeldingen:
            self.stdout.write(regel)
        # for

    def heeft_scores(self):
        return self._params.heeft_scores

    def heeft_uitslag(self):
        return self._params.heeft_uitslag

    def tel_deelnemers(self):
        return self._params.aantal_deelnemers

    def bepaal_wedstrijd_fase(self):
        return self._params.voortgang

    def get_indiv_deelnemers(self):
        """ geeft een lijst terug met op elke regel een mogelijk deelnemer
            volgorde is zoals weergegeven in het google sheet
        """
        return self._params.deelnemers

    def get_indiv_voorronde_uitslag(self):
        """ geeft een lijst terug met op elke regel een mogelijke voorronde uitslag:
            dit is de som van de twee voorronde scores plus de eventuele shootoff als decimaal

            de volgorde komt overeen met get_deelnemers()
        """
        data = self._params.voorronde_uitslag
        return data

    def get_indiv_voorronde_scores(self):
        """ geeft een lijst terug met op elke regel de mogelijke score van een deelnemer:
            [
                score ronde 1
                score ronde 2
                totaal score
                aantal 10-en        # leeg voor de Indoor
                aantal 9-ens        # leeg voor de Indoor
                aantal 8-en         # leeg voor de Indoor
            ]
        """
        return self._params.voorronde_scores

    def get_indiv_finales_uitslag(self):
        """ geeft de data van de finales terug, voor individuele Indoor wedstrijden
            data  = list[uitslag, ronde, ronde, ..] met
            uitslag = list['Goud', 'Zilver', 'Brons', '4e'] in verschillende volgordes
            ronde = ['[123456] Naam', '[234567] Naam', ..]
        """
        return self._params.finales_uitslag


class TestCompKampioenschapOpImportUitslagIndiv(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Maak Teams Excel (operations) """

    def _maak_bk_deelnemer(self, lid_nr, voornaam, achternaam, deelname_status=DEELNAME_ONBEKEND):
        sporter = Sporter.objects.create(
                            lid_nr=lid_nr,
                            voornaam=voornaam,
                            achternaam=achternaam,
                            email='',
                            geboorte_datum='1999-09-09',
                            geslacht='M',
                            sinds_datum='2019-01-01',
                            lid_tot_einde_jaar=2025,
                            bij_vereniging=self.ver)

        # geen para
        SporterVoorkeuren.objects.create(
                            sporter=sporter,
                            para_voorwerpen=False,
                            opmerking_para_sporter='')

        sporterboog = SporterBoog.objects.create(
                                sporter=sporter,
                                boogtype=self.boog_r,
                                voor_wedstrijd=True)

        deelnemer_bk = DeelnemerBK.objects.create(
                                kamp=self.kamp_bk,
                                sporterboog=sporterboog,
                                indiv_klasse=self.indiv_klasse,
                                indiv_klasse_volgende_ronde=self.indiv_klasse,
                                bij_vereniging=self.ver,
                                bevestiging_gevraagd_op='2000-01-01T00:00:00Z',
                                deelname=deelname_status,
                                gemiddelde=10.0)

    def setUp(self):
        self.functie_bko = maak_functie('BKO', 'BKO')

        self.ver = Vereniging.objects.create(
                                    ver_nr=1001,
                                    naam='Grote club',
                                    plaats='',
                                    regio=Regio.objects.get(regio_nr=106))

        self.comp = Competitie.objects.create(
                            begin_jaar=2025,
                            beschrijving='Comp18',
                            afstand='18')
        self.comp.refresh_from_db()

        self.rayon4 = Rayon.objects.get(rayon_nr=4)

        self.kamp_rk = KampRK.objects.create(
                            competitie=self.comp,
                            functie=self.functie_bko,
                            rayon=self.rayon4,
                            heeft_deelnemerslijst=True)

        self.kamp_bk = KampBK.objects.create(
                            competitie=self.comp,
                            functie=self.functie_bko,
                            heeft_deelnemerslijst=True)

        self.boog_r = BoogType.objects.get(afkorting='R')

        self.indiv_klasse = CompetitieIndivKlasse.objects.create(
                                    competitie=self.comp,
                                    boogtype=self.boog_r,
                                    is_ook_voor_rk_bk=True,
                                    volgorde=1,
                                    beschrijving='test',
                                    min_ag=0)

        self._maak_bk_deelnemer(100007, 'Zeven', 'Scoorder')
        self._maak_bk_deelnemer(100008, 'Acht', 'Scoorder', DEELNAME_NEE)
        self._maak_bk_deelnemer(100009, 'Negen', 'Scoorder', DEELNAME_JA)
        self._maak_bk_deelnemer(100010, 'Tien', 'Scoorder', DEELNAME_JA)

        self.bestand = Bestand.objects.create(
                                begin_jaar=self.comp.begin_jaar,
                                afstand=self.comp.afstand,
                                is_teams=False,
                                is_bk=True,
                                klasse_pk=self.indiv_klasse.pk,
                                rayon_nr=0,
                                fname='fname_1',
                                file_id='file_id_1')
        self.bestand.refresh_from_db()

        self.sheet_status = SheetStatus.objects.create(
                                bestand=self.bestand,
                                bevat_scores=False,
                                uitslag_is_compleet=False)

    def test_fout(self):
        params = SimpleNamespace(
                        heeft_scores=False,
                        heeft_uitslag=False,
                        aantal_deelnemers=0,
                        voortgang='Geen invoer',
                        deelnemers=[],
                        voorronde_uitslag=[],
                        voorronde_scores=[],
                        finales_blad=0,
                        finales_uitslag=[],
                        foutmeldingen=['[INFO] Dit is een test',
                                       '[DEBUG] {execute} Retrying in',])

        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.LeesIndivWedstrijdFormulier', new=MockLeesIndivWedstrijdFormulier):
            self.sheet_status.bestand.params = params
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)
        self.assertTrue(bevat_fout)
        self.assertEqual(blokjes_info[0][0], 'Fout: inlezen van Google Sheet is niet gelukt')

    def test_bk_geen_uitslag(self):
        ver_str = self.ver.ver_nr_en_naam()

        params = SimpleNamespace(
                        heeft_scores=False,
                        heeft_uitslag=False,
                        aantal_deelnemers=0,
                        voortgang='Geen invoer',
                        deelnemers=[
                            [100007, 'Zeven Scoorder', ver_str, '106', '', 7.0],
                            ['100008', 'Acht Scoorder', ver_str, '106', '', 8.0],
                            ['100009', 'Negen Scoorder', ver_str, '106', '', 9.0],
                            ['100010', 'Tien Scoorder', ver_str, '106', '', 10.0],
                        ],
                        voorronde_uitslag=[],
                        voorronde_scores=[],
                        finales_blad=0,
                        finales_uitslag=[],
                        foutmeldingen=[])

        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.LeesIndivWedstrijdFormulier',
                   new=MockLeesIndivWedstrijdFormulier):
            self.sheet_status.bestand.params = params
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)

        self.assertTrue(bevat_fout)
        for regels in blokjes_info:
            print(regels)

    def test_rk_met_fouten(self):
        ver_str = self.ver.ver_nr_en_naam()

        params = SimpleNamespace(
                        heeft_scores=False,
                        heeft_uitslag=False,
                        aantal_deelnemers=0,
                        voortgang='Geen invoer',
                        deelnemers=[
                            [100007, 'Zeven Scoorder', ver_str, '106', '', 7.0],
                            [],
                            [100011, 'Niet compleet'],
                        ],
                        voorronde_uitslag=[],
                        voorronde_scores=[],
                        finales_blad=0,
                        finales_uitslag=[],
                        foutmeldingen=[])

        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.LeesIndivWedstrijdFormulier',
                   new=MockLeesIndivWedstrijdFormulier):
            self.sheet_status.bestand.params = params
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_rk, self.indiv_klasse, self.sheet_status)

        self.assertTrue(bevat_fout)
        # for regels in blokjes_info:
        #     print(regels)

    def test_met_uitslag_18(self):
        ver_str = self.ver.ver_nr_en_naam()

        params = SimpleNamespace(
                        heeft_scores=False,
                        heeft_uitslag=False,
                        aantal_deelnemers=0,
                        voortgang='Geen invoer',
                        deelnemers=[
                            ['100007', 'Zeven Scoorder', ver_str, '106', '', 7.0],
                            ['100008', 'Acht Scoorder', ver_str, '106', '', 8.0],
                            ['100009', 'Negen Scoorder', ver_str, '106', '', 9.0],
                            ['100010', 'Tien Scoorder', ver_str, '106', '', 10.0],
                        ],
                        voorronde_uitslag=[
                            14,
                            17.002,
                            17.001,
                            # 18
                        ],
                        voorronde_scores=[
                            [7, ''],
                            [8, 9, 17],
                            [9, 8, 17],
                            # [10, 8],
                        ],
                        finales_blad=4,
                        finales_uitslag=[
                            ['Goud', 'Zilver', 'Brons', '4e'],
                            ['[100010] x', '[100009] y', '[100008] z', '[100007] Zeven Scoorder'],
                            [],  # 1/2 finale wordt niet gebruikt
                            ['[100010] x', '[100009] y', '[100008] z', '[100007] Fout'],
                        ],
                        foutmeldingen=[])

        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.LeesIndivWedstrijdFormulier',
                   new=MockLeesIndivWedstrijdFormulier):
            self.sheet_status.bestand.params = params
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)

        # for regels in blokjes_info:
        #     print(regels)
        #self.assertFalse(bevat_fout)

    def test_met_uitslag_25(self):
        ver_str = self.ver.ver_nr_en_naam()

        self.sheet_status.bestand.afstand = 25
        self.sheet_status.bestand.save()

        params = SimpleNamespace(
            heeft_scores=False,
            heeft_uitslag=False,
            aantal_deelnemers=0,
            voortgang='Geen invoer',
            deelnemers=[
                ['100007', 'Zeven Scoorder', ver_str, '106', '', 7.0],
                ['100008', 'Acht Scoorder', ver_str, '106', '', 8.0],
                ['100009', 'Negen Scoorder', ver_str, '106', '', 9.0],
                ['100010', 'Tien Scoorder', ver_str, '106', '', 10.0],
            ],
            voorronde_uitslag=[
                14,
                16,
                18.002,
                18.001
            ],
            voorronde_scores=[
                [7, 7, 14, '5', '4', 'error'],   # geen getal --> foutmelding
                [7, 7, 14, '25', '25', '3'],     # meer dan 50 --> foutmelding
            ],
            finales_blad=0,
            finales_uitslag=[],
            foutmeldingen=[])

        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.LeesIndivWedstrijdFormulier',
                   new=MockLeesIndivWedstrijdFormulier):
            self.sheet_status.bestand.params = params
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)

        # if bevat_fout:  # pragma: no cover
        #     for regels in blokjes_info:
        #         print(regels)
        # self.assertFalse(bevat_fout)

# end of file
