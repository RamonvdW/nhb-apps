# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies """

from django.utils import timezone
from django.templatetags.l10n import localize
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE, DEELNAME2STR
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMatch,
                               Kampioenschap, KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog)
from Geo.models import Rayon
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet
from Sporter.models import SporterVoorkeuren


class LeesIndivWedstrijdFormulier:

    def __init__(self, stdout, bestand: Bestand, sheet: StorageGoogleSheet):
        self.stdout = stdout
        self.sheet = sheet      # kan google sheets bijwerken
        self.afstand = bestand.afstand

        self.aantal_regels_deelnemers = 24          # maximum
        self.aantal_regels_reserves = 0

        self.klasse = None
        self.haalbare_titel = 'Kampioen'            # wordt bijgewerkt in laad_klasse
        self.kampioenschap = None
        self.limiet = 0                             # maximaal aantal deelnemers
        self.aantal_ingeschreven = 0
        self._max_naar_finales = 0

        self.ranges = {
            'titel': 'C2',
            'info': 'F4:F7',
            'bijgewerkt': 'A37',
            'voorronde_1': 'J11:J35',
            'voorronde_2': 'K11:K35',
            'uitslag_25m1p': 'R11:R35',
            'deelnemers': 'D11:I34',
            'haalbare_titel': 'U7',
            'finales16_8': 'C8:C53',        # 1/8 (laatste 16)
            'finales16_4': 'I11:I49',       # 1/4 (laatste 8)
            'finales16_2': 'O17:O43',       # 1/2 (laatste 4)
            'finales16_1': 'U25:U35',       # 1/1 (brons en gouden match)
            'finales16_uitslag': 'X25:X35',
            'finales8_4': 'C11:C49',        # 1/4 (laatste 8)
            'finales8_2': 'I17:I43',        # 1/2 (laatste 4)
            'finales8_1': 'O25:O35',        # 1/1 (brons en gouden match)
            'finales8_uitslag': 'R25:R35',
            'finales4_2': 'C17:C43',        # 1/2 (laatste 4)
            'finales4_1': 'I25:I35',        # 1/1 (brons en gouden match)
            'finales4_uitslag': 'L25:L35',
        }

        self._data_deelnemers = list()
        self._data_heeft_scores = False
        self._data_heeft_uitslag = False
        self._wedstrijd_voortgang = ''

        self._laad_sheet()

    def _check_input(self, cells_range):
        values = self.sheet.get_range(cells_range)
        if values:
            for row in values:
                for cell in row:
                    if cell:
                        # cell is niet leeg
                        return True
                # for
            # for
        return False

    def _check_input_on_sheet(self, sheet_name, range_name):
        # self.stdout.write('[DEBUG] check range %s op sheet %s' % (range_name, sheet_name))
        self.sheet.selecteer_sheet(sheet_name)
        return self._check_input(self.ranges[range_name])

    def _laad_sheet_indoor_finales(self):
        # zoek naar de uitslag
        # TODO: kunnen we dit verfijnen naar "bronzen finale" en "gouden finale"?
        if self._check_input_on_sheet('Finales 16', 'finales16_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            return

        if self._check_input_on_sheet('Finales 8', 'finales8_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            return

        if self._check_input_on_sheet('Finales 4', 'finales4_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            return

        # zoek naar de medaille finales
        if self._check_input_on_sheet('Finales 16', 'finales16_1'):
            self._wedstrijd_voortgang = 'Medaille finales'
            return

        if self._check_input_on_sheet('Finales 8', 'finales8_1'):
            self._wedstrijd_voortgang = 'Medaille finales'
            return

        if self._check_input_on_sheet('Finales 4', 'finales4_1'):
            self._wedstrijd_voortgang = 'Medaille finales'
            return

        # zoek naar de 1/2 finales
        if self._check_input_on_sheet('Finales 16', 'finales16_2'):
            self._wedstrijd_voortgang = '1/2 finales'
            return

        if self._check_input_on_sheet('Finales 8', 'finales8_2'):
            self._wedstrijd_voortgang = '1/2 finales'
            return

        if self._check_input_on_sheet('Finales 4', 'finales4_2'):
            self._wedstrijd_voortgang = '1/2 finales'
            return

        # zoek naar de 1/4 finales
        if self._check_input_on_sheet('Finales 16', 'finales16_4'):
            self._wedstrijd_voortgang = '1/4 finales'
            return

        if self._check_input_on_sheet('Finales 8', 'finales8_4'):
            self._wedstrijd_voortgang = '1/4 finales'
            return

        # zoek naar de 1/8 finales
        if self._check_input_on_sheet('Finales 16', 'finales16_8'):
            self._wedstrijd_voortgang = '1/8 finales'
            return

    def _laad_sheet(self):
        if self.afstand == 18:
            # Indoor
            self.sheet.selecteer_sheet('Voorronde')
        else:
            # 25m1pijl
            self.sheet.selecteer_sheet('Wedstrijd')

        self._data_deelnemers = self.sheet.get_range(self.ranges['deelnemers'])

        self._wedstrijd_voortgang = 'Geen invoer'

        if self._check_input(self.ranges['voorronde_1']):
            self._data_heeft_scores = True
            self._wedstrijd_voortgang = 'Voorronde 1'

            if self._check_input(self.ranges['voorronde_2']):
                self._wedstrijd_voortgang = 'Voorronde 2'

                if self.afstand == 25:
                    if self._check_input(self.ranges['uitslag_25m1p']):
                        self._wedstrijd_voortgang = 'Uitslag bekend'
                        self._data_heeft_uitslag = True
                else:
                    # bekijk de finales (alleen voor de Indoor)
                    # dit kan op 3 van de finale-sheets staan
                    self._laad_sheet_indoor_finales()
            # for

    def heeft_scores(self):
        return self._data_heeft_scores

    def heeft_uitslag(self):
        return self._data_heeft_uitslag

    def tel_deelnemers(self):
        return len(self._data_deelnemers)

    def bepaal_wedstrijd_fase(self):
        return self._wedstrijd_voortgang


# end of file
