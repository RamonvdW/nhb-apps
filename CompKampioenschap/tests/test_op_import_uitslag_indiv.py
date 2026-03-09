# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from BasisTypen.models import BoogType
from Competitie.models import Competitie, CompetitieIndivKlasse
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import importeer_sheet_uitslag_indiv
from CompLaagBond.models import KampBK, DeelnemerBK
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from GoogleDrive.models import Bestand
from Sporter.models import Sporter, SporterBoog, SporterVoorkeuren
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from unittest.mock import patch


class SheetMock:

    def __init__(self, _stdout, verbose=True, sheet_ranges=None):
        self.file_id = ''
        self.selected_sheet = ''
        self.verbose = verbose
        self.sheet_ranges = sheet_ranges

    def selecteer_file(self, file_id: str):
        self.file_id = file_id

    def selecteer_sheet(self, sheet_name: str):
        if self.verbose:
            print('[DEBUG] {SheetMock} selecteer_sheet: %s' % repr(sheet_name))
        self.selected_sheet = sheet_name

    def get_range(self, range_a1: str):
        if self.verbose:
            print('[DEBUG] {SheetMock} get_range: %s from sheet %s' % (repr(range_a1), repr(self.selected_sheet)))

        try:
            ranges = self.sheet_ranges[self.selected_sheet]
        except KeyError:
            print('[ERROR] {SheetMock} No sheet_ranges for sheet %s' % repr(self.selected_sheet))
            values = [[]]
        else:
            try:
                values = ranges[range_a1]
            except KeyError:
                print('[ERROR] {SheetMock} Range %s not found on sheet %s' % (repr(range_a1), repr(self.selected_sheet)))
                values = [[]]

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


class TestCompKampioenschapOpImportUitslagIndiv(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Importeer Uitslag Individueel """

    voorronde = {
        'D11:I34': [  # deelnemers
            ['100010', 'Tien Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
            ['100009', 'Negen Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
            ['100008', 'Acht Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
            ['100007', 'Zeven Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
        ],
        'J11:J35': [  # voorronde 1 scores
            [10],
            [9],
            [8],
            [7],
        ],
        'K11:K35': [  # voorronde 2 scores
            [10],
            [9],
            [8],
            [7],
        ],
        'J11:O34': [  # 1e, 2e, totaal, 10-en, 9-en, 8-en
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14],
        ],
        'S11:S34': [  # uitslag, inclusief shoot-off resultaat als decimaal
            [20],
            [18.001],
            [18],
            [14],
        ],
    }

    sheet_ranges_bezig4 = {
        'Voorronde': voorronde,
        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
        },
        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
        },
        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'H25:H35': [        # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5*[[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'I25:I35': [        # setpunten finales
                [6],  # 25: gouden finale
                [''],
                [0],  # 27: gouden finale
                *5*[[]],
                [4],  # 33: bronzen finale
                [],
                [6],  # 35: brozen finale
            ],
            'C17:C43': [  # setpunten 1/2 finale
                [6],  # 17
                [],
                [4],  # 19
                *21*[[]],
                [5],  # 41
                [],
                [5],  # 43
            ],
            'B17:B43': [  # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100009] Negen Scoorder'],  # 19
                *21 * [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100007] Zeven Scoorder'],  # 43
            ],
        },
    }

    sheet_ranges_finales4 = {
        'Voorronde': voorronde,
        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
        },
        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
        },
        'Finales 4': {
            'L25:L35': [        # uitslag finales: "Zilver", etc.
                ['Goud'],  # 25: gouden finale
                [],
                ['Zilver'],  # 27: gouden finale
                *5*[[]],
                ['4e'],  # 33: bronzen finale
                [],
                ['Brons'],  # 35: brozen finale
            ],
            'H25:H35': [        # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5*[[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'I25:I35': [        # setpunten finales
                [6],  # 25: gouden finale
                [''],
                [0],  # 27: gouden finale
                *5*[[]],
                [4],  # 33: bronzen finale
                [],
                [6],  # 35: brozen finale
            ],
            'C17:C43': [  # setpunten 1/2 finale
                [6],  # 17
                [],
                [4],  # 19
                *21*[[]],
                [5],  # 41
                [],
                [5],  # 43
            ],
            'B17:B43': [  # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100009] Negen Scoorder'],  # 19
                *21 * [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100007] Zeven Scoorder'],  # 43
            ],
        },
    }

    sheet_ranges_finales8 = {
        # Wedstrijd is voor 25m1pijl
        'Wedstrijd': {
        },

        # Voorronde is voor Indoor
        'Voorronde': {
            'D11:I34': [        # deelnemers
                ['100010', 'Tien Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
                ['100009', 'Negen Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
                ['100008', 'Acht Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
                ['100007', 'Zeven Scoorder', '[1001] Grote club', 'G', 'H', 'I'],
            ],
            'J11:J35': [        # voorronde 1 scores
                [10],
                [9],
                [8],
                [7],
            ],
            'K11:K35': [        # voorronde 2 scores
                [10],
                [9],
                [8],
                [7],
            ],
            'J11:O34': [        # 1e, 2e, totaal, 10-en, 9-en, 8-en
                [10, 10, 20],
                [9, 9, 18],
                [8, 10, 18],
                [7, 7, 14],
            ],
            'S11:S34': [        # uitslag, inclusief shoot-off resultaat als decimaal
                [20],
                [18.001],
                [18],
                [14],
            ],
        },

        # Finales zijn alleen voor de Indoor
        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
        },

        'Finales 8': {
            'R25:R35': [            # uitslag finales: "Zilver", etc.
                ['Goud'],    # 25: gouden finale
                [],
                ['Zilver'],  # 27: gouden finale
                *5*[[]],
                ['4e'],      # 33: bronzen finale
                [],
                ['Brons'],   # 35: brozen finale
            ],
            'N25:N35': [            # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5 * [[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'H17:H43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21* [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'B11:B49': [            # deelnemers 1/4 finale
                ['[100010] Tien Scoorder'],  # 11
                [],
                ['BYE'],                     # 13
                *9*[[]],
                ['[100009] Negen Scoorder'], # 23
                [],
                ['BYE'],                     # 25
                *9*[[]],
                ['[100008] Acht Scoorder'],  # 35
                [],
                ['BYE'],                     # 37
                *9*[[]],
                ['[100007] Zeven Scoorder'], # 47
                [],
                ['BYE'],                     # 49
            ],
        },

        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'I25:I35': [        # setpunten finales
                [6],  # 25: gouden finale
                [''],
                [0],  # 27: gouden finale
                *5*[[]],
                [4],  # 33: bronzen finale
                [],
                [6],  # 35: brozen finale
            ],
        },
    }

    def _maak_bk_deelnemer(self, lid_nr, voornaam, achternaam):
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
                                #deelname=DEELNAME_ONBEKEND,
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
        self._maak_bk_deelnemer(100008, 'Acht', 'Scoorder')
        self._maak_bk_deelnemer(100009, 'Negen', 'Scoorder')
        self._maak_bk_deelnemer(100010, 'Tien', 'Scoorder')

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

    def test_finals4(self):
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales4)
        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.StorageGoogleSheet', return_value=my_sheet):
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)
        if bevat_fout:      # pragma: no cover
            for regels in blokjes_info:
                print(regels)
        self.assertFalse(bevat_fout)

    def test_bezig4(self):
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_bezig4)
        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.StorageGoogleSheet', return_value=my_sheet):
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)
        if bevat_fout:      # pragma: no cover
            for regels in blokjes_info:
                print(regels)
        self.assertFalse(bevat_fout)

    def test_finals8(self):
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales8)
        with patch('CompKampioenschap.operations.importeer_uitslag_indiv.StorageGoogleSheet', return_value=my_sheet):
            bevat_fout, blokjes_info = importeer_sheet_uitslag_indiv(self.kamp_bk, self.indiv_klasse, self.sheet_status)
        self.assertFalse(bevat_fout)
        if bevat_fout:      # pragma: no cover
            for regels in blokjes_info:
                print(regels)
        self.assertFalse(bevat_fout)


# end of file
