# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import LeesIndivWedstrijdFormulier
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet
from TestHelpers.e2ehelpers import E2EHelpers
import io


class SheetMock(StorageGoogleSheet):

    def __init__(self, _stdout, verbose=True, sheet_ranges=None):
        super().__init__(_stdout, retry_delay=0.0001)
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

    def clear_range(self, range_a1: str):
        pass

    def wijzig_cellen(self, range_a1: str, values: list):
        pass

    def stuur_wijzigingen(self):
        pass

    def toon_sheet(self, sheet_name: str):
        pass

    def hide_sheet(self, sheet_name: str):
        pass


class TestCompKampioenschapOpWfIndivLees(E2EHelpers, TestCase):

    """ tests voor de CompKampioenschap module, operations Wedstrijdformulier Individueel Lees """

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

    sheet_ranges_finales4_medailles = {
        'Voorronde': voorronde,
        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
        },
        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
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
                *21*[[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100007] Zeven Scoorder'],  # 43
            ],
        },
    }

    sheet_ranges_finales4_halve = {
        'Voorronde': voorronde,
        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'O17:O43': None,    # setpunten 1/2 finale
        },
        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'I17:I43': None,    # setpunten 1/2 finale
        },
        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'H25:H35': None,    # deelnemers finales
            'I25:I35': None,    # setpunten finales
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
                *21*[[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100007] Zeven Scoorder'],  # 43
            ],
        },
    }

    sheet_ranges_finales4_uitslag = {
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
                [''],  # 33: bronzen finale
                [],
                ['Brons'],  # 35: brozen finale
            ],
            'H25:H35': [        # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *3*[[]],
                ['Bronzen finale'],
                [],
                ['BYE'],  # 33
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
                *21*[[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100007] Zeven Scoorder'],  # 43
            ],
        },
    }

    sheet_ranges_finales8_kwart = {
        'Voorronde': voorronde,

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'O17:O43': None,    # setpunten 1/2 finale
            'I11:I49': None,    # setpunten 1/4 finale
            'C8:C53': None,     # setpunten 1/8 finale
        },

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'I17:I43': None,    # setpunten 1/2 finale
            'C11:C49': [        # setpunten 1/4 finale
                [6],    # 11
                [],
                [0],    # 13
                *9*[[]],
                [6],    # 23
                [],
                [0],    # 25
                *9*[[]],
                [6],    # 35
                [],
                [0],    # 37
                *9*[[]],
                [6],    # 47
                [],
                [0],    # 49
            ],
            'B11:B49': [        # deelnemers 1/4 finale
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
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales8_halve = {
        'Voorronde': voorronde,

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'O17:O43': None,    # setpunten 1/2 finale
            'I11:I49': None,    # setpunten 1/4 finale
            'C8:C53': None,     # setpunten 1/8 finale
        },

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'N25:N35': None,    # deelnemers finales
            'H17:H43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21* [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'I17:I43': [        # setpunten 1/2 finale
                [0],  # 17
                [],
                [6],  # 19
                *21*[[]],
                [5],  # 41
                [],
                [5],  # 43
            ],
            'C11:C49': [        # setpunten 1/4 finale
                [6],    # 11
                [],
                [0],    # 13
                *9*[[]],
                [6],    # 23
                [],
                [0],    # 25
                *9*[[]],
                [6],    # 35
                [],
                [0],    # 37
                *9*[[]],
                [6],    # 47
                [],
                [0],    # 49
            ],
            'B11:B49': [        # deelnemers 1/4 finale
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
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales8_medailles = {
        'Voorronde': voorronde,

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'O17:O43': None,    # setpunten 1/2 finale
            'I11:I49': None,    # setpunten 1/4 finale
            'C8:C53': None,     # setpunten 1/8 finale
        },

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': [        # setpunten finales
                [0],  # 25
                [],
                [6],  # 27
                *5*[[]],
                [5],  # 33
                [],
                [5],  # 35
            ],
            'N25:N35': [            # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5*[[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'I17:I43': [            # setpunten 1/2 finale
                [0],  # 17
                [],
                [6],  # 19
                *21*[[]],
                [5],  # 41
                [],
                [5],  # 43
            ],
            'H17:H43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21*[[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'C11:C49': [  # setpunten 1/4 finale
                [6],  # 11
                [],
                [0],  # 13
                *9*[[]],
                [6],  # 23
                [],
                [0],  # 25
                *9*[[]],
                [6],  # 35
                [],
                [0],  # 37
                *9*[[]],
                [6],  # 47
                [],
                [0],  # 49
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
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales8_uitslag = {
        'Voorronde': voorronde,

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
                *5*[[]],
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
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales16_uitslag = {
        'Voorronde': voorronde,

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
        },

        'Finales 16': {
            'X25:X35': [            # uitslag finales: "Zilver", etc.
                ['Goud'],    # 25: gouden finale
                [],
                ['Zilver'],  # 27: gouden finale
                *5*[[]],
                ['4e'],      # 33: bronzen finale
                [],
                ['Brons'],   # 35: brozen finale
            ],
            'T25:T35': [            # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5*[[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'N17:N43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21* [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'H11:H49': [            # deelnemers 1/4 finale
                ['[100010] Tien Scoorder'],  # 11
                [],
                ['[100002] Twee Scoorder'],  # 13
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
            'B8:B52': [             # deelnemers 1/8 finale
                ['[100010] Tien Scoorder'],  # 8
                [],
                ['BYE'],  # 10
                *3*[[]],
                ['BYE'],  # 14
                [],
                ['BYE'],  # 16
                *3*[[]],
                ['[100009] Negen Scoorder'],  # 20
                [],
                ['BYE'],  # 22
                *3*[[]],
                ['BYE'],  # 26
                [],
                ['BYE'],  # 28
                *3*[[]],
                ['[100008] Acht Scoorder'],  # 32
                [],
                ['BYE'],  # 34
                *3*[[]],
                ['BYE'],  # 38
                [],
                ['BYE'],  # 40
                *3*[[]],
                ['[100007] Zeven Scoorder'],  # 44
                [],
                ['BYE'],  # 46
                *3*[[]],
                ['BYE'],  # 50
                [],
                ['BYE'],  # 52
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

    sheet_ranges_finales16_medailles = {
        'Voorronde': voorronde,

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
        },

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': [        # setpunten finales
                [0],
                [''],
                [6],
                *5*[[]],
                [5],
                [''],
                [5],
            ],
            'T25:T35': [            # deelnemers finales
                ['[100010] Tien Scoorder'],  # 25
                [],
                ['[100007] Zeven Scoorder'],  # 27
                *5*[[]],
                ['[100008] Acht Scoorder'],  # 33
                [],
                ['[100009] Negen Scoorder'],  # 35
            ],
            'N17:N43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21* [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'H11:H49': [            # deelnemers 1/4 finale
                ['[100010] Tien Scoorder'],  # 11
                [],
                ['[100002] Twee Scoorder'],  # 13
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
            'B8:B52': [             # deelnemers 1/8 finale
                ['[100010] Tien Scoorder'],  # 8
                [],
                ['BYE'],  # 10
                *3*[[]],
                ['BYE'],  # 14
                [],
                ['BYE'],  # 16
                *3*[[]],
                ['[100009] Negen Scoorder'],  # 20
                [],
                ['BYE'],  # 22
                *3*[[]],
                ['BYE'],  # 26
                [],
                ['BYE'],  # 28
                *3*[[]],
                ['[100008] Acht Scoorder'],  # 32
                [],
                ['BYE'],  # 34
                *3*[[]],
                ['BYE'],  # 38
                [],
                ['BYE'],  # 40
                *3*[[]],
                ['[100007] Zeven Scoorder'],  # 44
                [],
                ['BYE'],  # 46
                *3*[[]],
                ['BYE'],  # 50
                [],
                ['BYE'],  # 52
            ],
        },

        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
        },
    }

    sheet_ranges_finales16_halve = {
        'Voorronde': voorronde,

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'I17:I43': None,    # setpunten 1/2 finale
            'C11:C49': None,    # setpunten 1/4 finale
        },

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'T25:T35': None,    # deelnemers finales
            'O17:O43': [        # setpunten 1/2 finale
                [''],  # 17
                [''],
                [''],  # 19
                *21*[[]],
                [2],  # 41
                [],
                [0],  # 43
            ],
            'N17:N43': [            # deelnemers 1/2 finale
                ['[100010] Tien Scoorder'],  # 17
                [],
                ['[100007] Zeven Scoorder'],  # 19
                *21* [[]],
                ['[100008] Acht Scoorder'],  # 41
                [],
                ['[100009] Negen Scoorder'],  # 43
            ],
            'I11:I49': [            # setpunten 1/4 finale
                [6],
                [''],
                [2],
                *9*[[]],
                [0],
                [''],
                [1],
                *9 * [[]],
                [1],
                [''],
                [0],
                *9 * [[]],
                [6],
                [''],
                [0],
            ],
            'H11:H49': [            # deelnemers 1/4 finale
                ['[100010] Tien Scoorder'],  # 11
                [],
                ['[100002] Twee Scoorder'],  # 13
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
            'B8:B52': [             # deelnemers 1/8 finale
                ['[100010] Tien Scoorder'],  # 8
                [],
                ['BYE'],  # 10
                *3*[[]],
                ['BYE'],  # 14
                [],
                ['BYE'],  # 16
                *3*[[]],
                ['[100009] Negen Scoorder'],  # 20
                [],
                ['BYE'],  # 22
                *3*[[]],
                ['BYE'],  # 26
                [],
                ['BYE'],  # 28
                *3*[[]],
                ['[100008] Acht Scoorder'],  # 32
                [],
                ['BYE'],  # 34
                *3*[[]],
                ['BYE'],  # 38
                [],
                ['BYE'],  # 40
                *3*[[]],
                ['[100007] Zeven Scoorder'],  # 44
                [],
                ['BYE'],  # 46
                *3*[[]],
                ['BYE'],  # 50
                [],
                ['BYE'],  # 52
            ],
        },

        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales16_kwart = {
        'Voorronde': voorronde,

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'I17:I43': None,    # setpunten 1/2 finale
            'C11:C49': None,    # setpunten 1/4 finale
        },

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'T25:T35': None,    # deelnemers finales
            'O17:O43': None,    # setpunten 1/2 finale
            'N17:N43': None,    # deelnemers 1/2 finale
            'I11:I49': [            # setpunten 1/4 finale
                [6],
                [''],
                [2],
                *9*[[]],
                [0],
                [''],
                [1],
                *9 * [[]],
                [1],
                [''],
                [0],
                *9 * [[]],
                [6],
                [''],
                [0],
            ],
            'H11:H49': [            # deelnemers 1/4 finale
                ['[100010] Tien Scoorder'],  # 11
                [],
                ['[100002] Twee Scoorder'],  # 13
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
            'B8:B52': [             # deelnemers 1/8 finale
                ['[100010] Tien Scoorder'],  # 8
                [],
                ['BYE'],  # 10
                *3*[[]],
                ['BYE'],  # 14
                [],
                ['BYE'],  # 16
                *3*[[]],
                ['[100009] Negen Scoorder'],  # 20
                [],
                ['BYE'],  # 22
                *3*[[]],
                ['BYE'],  # 26
                [],
                ['BYE'],  # 28
                *3*[[]],
                ['[100008] Acht Scoorder'],  # 32
                [],
                ['BYE'],  # 34
                *3*[[]],
                ['BYE'],  # 38
                [],
                ['BYE'],  # 40
                *3*[[]],
                ['[100007] Zeven Scoorder'],  # 44
                [],
                ['BYE'],  # 46
                *3*[[]],
                ['BYE'],  # 50
                [],
                ['BYE'],  # 52
            ],
        },

        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_finales16_achtste = {
        'Voorronde': voorronde,

        'Finales 8': {
            'R25:R35': None,    # uitslag finales: "Zilver", etc.
            'O25:O35': None,    # setpunten finales
            'I17:I43': None,    # setpunten 1/2 finale
            'C11:C49': None,    # setpunten 1/4 finale
        },

        'Finales 16': {
            'X25:X35': None,    # uitslag finales: "Zilver", etc.
            'U25:U35': None,    # setpunten finales
            'T25:T35': None,    # deelnemers finales
            'O17:O43': None,    # setpunten 1/2 finale
            'N17:N43': None,    # deelnemers 1/2 finale
            'I11:I49': None,    # setpunten 1/4 finale
            'H11:H49': None,    # deelnemers 1/4 finale
            'C8:C53': [
                [6],  # 8
                [],
                [''],  # 10
                *3 * [[]],
                [0],  # 14
                [],
                [0],  # 16
                *3 * [[]],
                [6],  # 20
                [],
                [0],  # 22
                *3 * [[]],
                [0],  # 26
                [],
                [0],  # 28
                *3 * [[]],
                [6],  # 32
                [],
                [0],  # 34
                *3 * [[]],
                [0],  # 38
                [],
                [0],  # 40
                *3 * [[]],
                [6],  # 44
                [],
                [0],  # 46
                *3 * [[]],
                [0],  # 50
                [],
                [0],  # 52
            ],
            'B8:B52': [         # deelnemers 1/8 finale
                ['[100010] Tien Scoorder'],  # 8
                [],
                ['BYE'],  # 10
                *3*[[]],
                ['BYE'],  # 14
                [],
                ['BYE'],  # 16
                *3*[[]],
                ['[100009] Negen Scoorder'],  # 20
                [],
                ['BYE'],  # 22
                *3*[[]],
                ['BYE'],  # 26
                [],
                ['BYE'],  # 28
                *3*[[]],
                ['[100008] Acht Scoorder'],  # 32
                [],
                ['BYE'],  # 34
                *3*[[]],
                ['BYE'],  # 38
                [],
                ['BYE'],  # 40
                *3*[[]],
                ['[100007] Zeven Scoorder'],  # 44
                [],
                ['BYE'],  # 46
                *3*[[]],
                ['BYE'],  # 50
                [],
                ['BYE'],  # 52
            ],
        },

        'Finales 4': {
            'L25:L35': None,    # uitslag finales: "Zilver", etc.
            'I25:I35': None,    # setpunten finales
            'C17:C43': None,    # setpunten 1/2 finale
        },
    }

    sheet_ranges_25_geen_deelnemers = {
        'Wedstrijd': {
            'D11:I34': [  # deelnemers
            ],
            'J11:J35': [  # scores 1e voorronde
            ],
            'K11:K35': [  # scores 2e voorronde
            ],
        }
    }

    sheet_ranges_25_geen_invoer = {
        'Wedstrijd': {
            'D11:I34': [        # deelnemers
                # D = bondsnummer; E = naam; F = vereniging; G = regio; H = label; I = gemiddelde
                ['100010', 'Tien Scoorder',  '[1001] Grote club', '101', 'Kampioen regio 101', '10,0'],
                ['100009', 'Negen Scoorder', '[1001] Grote club', '101', 'H', '9,0'],
                ['100008', 'Acht Scoorder',  '[1001] Grote club', '101', 'H', '8,0'],
                ['100007', 'Zeven Scoorder', '[1001] Grote club', '101', 'H', '7,000'],
            ],
            'J11:J35': [        # scores 1e voorronde
            ],
            'K11:K35': [        # scores 2e voorronde
            ],
        }
    }

    sheet_ranges_25_voorronde1 = {
        'Wedstrijd': {
            'D11:I34': [        # deelnemers
                # D = bondsnummer; E = naam; F = vereniging; G = regio; H = label; I = gemiddelde
                ['100010', 'Tien Scoorder',  '[1001] Grote club', '101', 'Kampioen regio 101', '10,0'],
                ['100009', 'Negen Scoorder', '[1001] Grote club', '101', 'H', '9,0'],
                ['100008', 'Acht Scoorder',  '[1001] Grote club', '101', 'H', '8,0'],
                ['100007', 'Zeven Scoorder', '[1001] Grote club', '101', 'H', '7,000'],
            ],
            'J11:J35': [        # scores 1e voorronde
                ['100'],
                ['90'],
                [''],  # no show
                ['70'],
            ],
            'K11:K35': [        # scores 2e voorronde
            ],
        }
    }

    sheet_ranges_25_voorronde2 = {
        'Wedstrijd': {
            'D11:I34': [        # deelnemers
                # D = bondsnummer; E = naam; F = vereniging; G = regio; H = label; I = gemiddelde
                ['100010', 'Tien Scoorder',  '[1001] Grote club', '101', 'Kampioen regio 101', '10,0'],
                ['100009', 'Negen Scoorder', '[1001] Grote club', '101', 'H', '9,0'],
                ['100008', 'Acht Scoorder',  '[1001] Grote club', '101', 'H', '8,0'],
                ['100007', 'Zeven Scoorder', '[1001] Grote club', '101', 'H', '7,000'],
            ],
            'J11:J35': [        # scores 1e voorronde
                [100],
                [90],
                [''],     # no show
                [70],
            ],
            'K11:K35': [        # scores 2e voorronde
                [100],
            ],
            'J11:O34': [        # volledige uitslag
                # 1e, 2e, totaal, 10-en, 9-en, 8-en
                [90, 90, 180, 40, 10, ''],
                [90, 90, 180, 39, 11, ''],
                [''],  # no show
                [70, 70, 140, 20, 25, 4],
            ],
            'S11:S34': [         # resultaat (kolom "sorteer mij")
            ],
        }
    }

    sheet_ranges_25_uitslag = {
        'Wedstrijd': {
            'D11:I34': [        # deelnemers
                # D = bondsnummer; E = naam; F = vereniging; G = regio; H = label; I = gemiddelde
                ['100010', 'Tien Scoorder',  '[1001] Grote club', '101', 'Kampioen regio 101', '10,0'],
                ['100009', 'Negen Scoorder', '[1001] Grote club', '101', 'H', '9,0'],
                ['100008', 'Acht Scoorder',  '[1001] Grote club', '101', 'H', '8,0'],
                ['100007', 'Zeven Scoorder', '[1001] Grote club', '101', 'H', '7,000'],
                [],             # voor coverage in tel_deelnemers
            ],
            'J11:J35': [        # scores 1e voorronde
                [100],
                [90],
                [''],     # no show
                [70],
            ],
            'K11:K35': [        # scores 2e voorronde
                [100],
            ],
            'J11:O34': [        # volledige uitslag
                # 1e, 2e, totaal, 10-en, 9-en, 8-en
                [90, 90, 180, 40, 10, ''],
                [90, 90, 180, 39, 11, ''],
                ['', '', '', '', '', ''],   # no show
                [70, 70, 140, 20, 25, 4],
            ],
            'S11:S34': [         # resultaat (kolom "sorteer mij")
                [180.4010],
                [180.3911],
                [''],
                [140.202504],
            ],
        }
    }

    def setUp(self):
        # self.comp = Competitie.objects.create(
        #                     begin_jaar=2025,
        #                     beschrijving='Comp18',
        #                     afstand='18')
        # self.comp.refresh_from_db()
        #
        # self.boog_r = BoogType.objects.get(afkorting='R')
        #
        # self.indiv_klasse = CompetitieIndivKlasse.objects.create(
        #                             competitie=self.comp,
        #                             boogtype=self.boog_r,
        #                             is_ook_voor_rk_bk=True,
        #                             volgorde=1,
        #                             beschrijving='test',
        #                             min_ag=0)

        self.bestand18 = Bestand.objects.create(
                                begin_jaar=2025,
                                afstand=18,
                                is_teams=False,
                                is_bk=True,
                                klasse_pk=1,
                                rayon_nr=0,
                                fname='fname_18',
                                file_id='file_id_18')
        self.bestand18.refresh_from_db()

        self.sheet_status18 = SheetStatus.objects.create(
                                bestand=self.bestand18,
                                bevat_scores=False,
                                uitslag_is_compleet=False)

        self.bestand25 = Bestand.objects.create(
                                begin_jaar=2025,
                                afstand=25,
                                is_teams=False,
                                is_bk=False,
                                klasse_pk=1,
                                rayon_nr=1,
                                fname='fname_25',
                                file_id='file_id_25')
        self.bestand25.refresh_from_db()

        self.sheet_status25 = SheetStatus.objects.create(
                                bestand=self.bestand18,
                                bevat_scores=False,
                                uitslag_is_compleet=False)

    def test_geen_deelnemers(self):
        stdout = OutputWrapper(io.StringIO())
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_25_geen_deelnemers)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand25, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Buiten gebruik')
        self.assertFalse(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())
        self.assertEqual(lees.tel_deelnemers(), 0)

        deelnemers = lees.get_indiv_deelnemers()
        self.assertEqual(deelnemers, [])

    def test_geen_invoer(self):
        stdout = OutputWrapper(io.StringIO())
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_25_geen_invoer)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand25, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Geen invoer')
        self.assertFalse(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())
        self.assertEqual(lees.tel_deelnemers(), 4)

        deelnemers = lees.get_indiv_deelnemers()
        self.assertEqual(deelnemers, [
            ['100010', 'Tien Scoorder', '[1001] Grote club', '101', 'Kampioen regio 101', '10,0'],
            ['100009', 'Negen Scoorder', '[1001] Grote club', '101', 'H', '9,0'],
            ['100008', 'Acht Scoorder', '[1001] Grote club', '101', 'H', '8,0'],
            ['100007', 'Zeven Scoorder', '[1001] Grote club', '101', 'H', '7,000']
        ])

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [])

        uitslag = lees.get_indiv_voorronde_uitslag()
        self.assertEqual(uitslag, [])

    def test_voorronde_1(self):
        stdout = OutputWrapper(io.StringIO())
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_25_voorronde1)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand25, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Voorronde 1')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [])

        uitslag = lees.get_indiv_voorronde_uitslag()
        self.assertEqual(uitslag, [])

    def test_voorronde_2(self):
        stdout = OutputWrapper(io.StringIO())
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_25_voorronde2)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand25, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Voorronde 2')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
                [90, 90, 180, 40, 10, ''],
                [90, 90, 180, 39, 11, ''],
                [''],
                [70, 70, 140, 20, 25, 4],
        ])

        uitslag = lees.get_indiv_voorronde_uitslag()
        self.assertEqual(uitslag, [])

    def test_uitslag(self):
        stdout = OutputWrapper(io.StringIO())
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_25_uitslag)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand25, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Uitslag bekend')
        self.assertTrue(lees.heeft_scores())
        self.assertTrue(lees.heeft_uitslag())

        uitslag = lees.get_indiv_voorronde_uitslag()
        self.assertEqual(uitslag, [180.401, 180.3911, '', 140.202504])

        res = lees.get_indiv_finales_uitslag()
        self.assertEqual(res, [])

    def test_indoor_finales4(self):
        stdout = OutputWrapper(io.StringIO())

        # uitslag
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales4_uitslag)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Uitslag bekend')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertTrue(lees.heeft_uitslag())
        res = lees.get_indiv_finales_uitslag()
        # print(repr(res))

        # extra coverage
        LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        # medaille finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales4_medailles)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Medaille finales')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertFalse(lees.heeft_uitslag())

        # 1/2 finale
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales4_halve)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/2 finales')

    def test_indoor_finales8(self):
        stdout = OutputWrapper(io.StringIO())

        # 1/4 finale
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales8_kwart)
        # lees_oppervlakkig stuurt inlezen finales
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/4 finales')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertFalse(lees.heeft_uitslag())

        # 1/2 finale
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales8_halve)
        # lees_oppervlakkig stuurt inlezen finales
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/2 finales')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertFalse(lees.heeft_uitslag())

        # medaille finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales8_medailles)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Medaille finales')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        # uitslag
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales8_uitslag)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Uitslag bekend')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertTrue(lees.heeft_uitslag())
        res = lees.get_indiv_finales_uitslag()
        # print(repr(res))
        self.assertEqual(len(res), 4)       # uitslag, finales, 1/2, 1/4
        self.assertEqual(res[0], ['Goud', 'Zilver', '4e', 'Brons'])
        self.assertEqual(res[1], ['[100010] Tien Scoorder', '[100007] Zeven Scoorder', '[100008] Acht Scoorder', '[100009] Negen Scoorder'])
        self.assertEqual(res[2], ['[100010] Tien Scoorder', '[100007] Zeven Scoorder', '[100008] Acht Scoorder', '[100009] Negen Scoorder'])
        self.assertEqual(res[3], ['[100010] Tien Scoorder', 'BYE', '[100009] Negen Scoorder', 'BYE', '[100008] Acht Scoorder', 'BYE', '[100007] Zeven Scoorder', 'BYE'])

        # extra coverage
        LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

    def test_indoor_finales16(self):
        stdout = OutputWrapper(io.StringIO())

        # uitslag
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales16_uitslag)
        # lees_oppervlakkig stuurt inlezen finales
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Uitslag bekend')
        self.assertTrue(lees.heeft_scores())

        scores = lees.get_indiv_voorronde_scores()
        self.assertEqual(scores, [
            [10, 10, 20],
            [9, 9, 18],
            [8, 10, 18],
            [7, 7, 14]
        ])

        self.assertTrue(lees.heeft_uitslag())
        res = lees.get_indiv_finales_uitslag()
        # print(repr(res))

        # extra coverage
        LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=True)

        # medaille finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales16_medailles)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, 'Medaille finales')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        # 1/2 finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales16_halve)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/2 finales')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        # 1/4 finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales16_kwart)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/4 finales')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

        # 1/8 finales
        my_sheet = SheetMock(None, verbose=False, sheet_ranges=self.sheet_ranges_finales16_achtste)
        lees = LeesIndivWedstrijdFormulier(stdout, self.bestand18, my_sheet, lees_oppervlakkig=False)

        fase = lees.bepaal_wedstrijd_fase()
        self.assertEqual(fase, '1/8 finales')
        self.assertTrue(lees.heeft_scores())
        self.assertFalse(lees.heeft_uitslag())

# end of file
