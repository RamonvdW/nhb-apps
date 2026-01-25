# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet


class LeesIndivWedstrijdFormulier:

    def __init__(self, stdout, bestand: Bestand, sheet: StorageGoogleSheet, lees_oppervlakkig: bool):
        self.stdout = stdout
        self.sheet = sheet      # kan google sheets bijwerken
        self.afstand = bestand.afstand
        self.lees_oppervlakkig = lees_oppervlakkig

        self.ranges = {
            'deelnemers': 'D11:I34',
            'voorronde_1': 'J11:J35',
            'voorronde_2': 'K11:K35',
            'voorronde_uitslag': 'S11:S34',
            'voorronde_25m_tellingen': 'M11:O34',   # 10-en, 9-ens, 8-en
            'finales16_8': 'C8:C53',                # 1/8 (laatste 16)
            'finales16_4': 'I11:I49',               # 1/4 (laatste 8)
            'finales16_2': 'O17:O43',               # 1/2 (laatste 4)
            'finales16_1': 'U25:U35',               # 1/1 (brons en gouden match)
            'finales16_uitslag': 'X25:X35',
            'finales8_4': 'C11:C49',                # 1/4 (laatste 8)
            'finales8_2': 'I17:I43',                # 1/2 (laatste 4)
            'finales8_1': 'O25:O35',                # 1/1 (brons en gouden match)
            'finales8_uitslag': 'R25:R35',
            'finales4_2': 'C17:C43',                # 1/2 (laatste 4)
            'finales4_1': 'I25:I35',                # 1/1 (brons en gouden match)
            'finales4_uitslag': 'L25:L35',
            'deelnemers_finales16_1': 'T25:T35',
            'deelnemers_finales16_2': 'N17:N43',
            'deelnemers_finales16_4': 'H11:H49',
            'deelnemers_finales16_8': 'B8:B52',
            'deelnemers_finales8_1': 'N25:N35',
            'deelnemers_finales8_2': 'H17:H43',
            'deelnemers_finales8_4': 'B11:B49',
            'deelnemers_finales4_1': 'H25:H35',
            'deelnemers_finales4_2': 'B17:B43',
        }

        self._data_deelnemers = list()
        self._data_heeft_scores = False
        self._data_heeft_uitslag = False
        self.finales_blad = 0
        self._data_scores_voorronde = list()
        self._data4range = dict()     # [range_name] = range_cells
        self._wedstrijd_voortgang = ''

        self.sheet.selecteer_file(bestand.file_id)
        self._laad_sheet()

    def _check_input(self, range_name):
        cells_range = self.ranges[range_name]
        values = self.sheet.get_range(cells_range)
        self._data4range[range_name] = values
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
        return self._check_input(range_name)

    def _laad_sheet_indoor_finales(self):
        # zoek naar de uitslag

        self.finales_blad = 0

        # TODO: kunnen we dit verfijnen naar "bronzen finale" en "gouden finale"?
        if self._check_input_on_sheet('Finales 16', 'finales16_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            self.finales_blad = 16       # de rest van het finales 16 blad halen

            # lees de rest van de uitslag
            if not self.lees_oppervlakkig:
                self._check_input('deelnemers_finales16_1')
                self._check_input('deelnemers_finales16_2')
                self._check_input('deelnemers_finales16_4')
                self._check_input('deelnemers_finales16_8')
            return

        if self._check_input_on_sheet('Finales 8', 'finales8_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            self.finales_blad = 8        # de rest van het finales 8 blad halen

            # lees de rest van de uitslag
            if not self.lees_oppervlakkig:
                self._check_input('deelnemers_finales8_1')
                self._check_input('deelnemers_finales8_2')
                self._check_input('deelnemers_finales8_4')
            return

        if self._check_input_on_sheet('Finales 4', 'finales4_uitslag'):
            self._wedstrijd_voortgang = 'Uitslag bekend'
            self._data_heeft_uitslag = True
            self.finales_blad = 4        # de rest van het finales 4 blad halen

            # lees de rest van de uitslag
            if not self.lees_oppervlakkig:
                self._check_input('deelnemers_finales4_1')
                self._check_input('deelnemers_finales4_2')
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

        if self._check_input('voorronde_1'):
            self._data_heeft_scores = True
            self._wedstrijd_voortgang = 'Voorronde 1'

            if self._check_input('voorronde_2'):
                self._wedstrijd_voortgang = 'Voorronde 2'

                self._data_voorronde_uitslag = self.sheet.get_range(self.ranges['voorronde_uitslag'])

                if self.afstand == 25:
                    self._data_heeft_uitslag = True
                    self._wedstrijd_voortgang = 'Uitslag bekend'
                else:
                    # alleen voor de Indoor, lees ook de finales
                    self._laad_sheet_indoor_finales()
            # for

    def heeft_scores(self):
        return self._data_heeft_scores

    def heeft_uitslag(self):
        return self._data_heeft_uitslag

    def tel_deelnemers(self):
        aantal = 0
        for row in self._data_deelnemers:
            if len(row) > 0:
                aantal += 1
        # for
        return aantal

    def bepaal_wedstrijd_fase(self):
        return self._wedstrijd_voortgang

    def get_indiv_deelnemers(self):
        """ geeft een lijst terug met op elke regel een mogelijk deelnemer
            volgorde is zoals weergegeven in het google sheet
        """
        return self._data_deelnemers

    def get_indiv_voorronde_uitslag(self):
        """ geeft een lijst terug met op elke regel een mogelijke voorronde uitslag
            dit is de som van de twee voorronde scores plus de eventuele shootoff als decimaal

            de volgorde komt overeen met get_deelnemers()
        """
        data = self._data_voorronde_uitslag
        # collapsed the sub-lists for single-column data sets
        for i in range(len(data)):
            i_len = len(data[i])
            if i_len == 1:
                data[i] = data[i][0]
        # for
        return data

    def get_indiv_finales_uitslag(self):
        """ geeft de data van de finales terug, voor individuele Indoor wedstrijden
        """
        if self.finales_blad == 16:
            data = [
                self._data4range['finales16_uitslag'],
                self._data4range['deelnemers_finales16_1'],
                self._data4range['deelnemers_finales16_2'],
                self._data4range['deelnemers_finales16_4'],
                self._data4range['deelnemers_finales16_8'],
            ]
        elif self.finales_blad == 8:
            data = [
                self._data4range['finales8_uitslag'],
                self._data4range['deelnemers_finales8_1'],
                self._data4range['deelnemers_finales8_2'],
                self._data4range['deelnemers_finales8_4'],
            ]
        elif self.finales_blad == 4:
            data = [
                self._data4range['finales4_uitslag'],
                self._data4range['deelnemers_finales4_1'],
                self._data4range['deelnemers_finales4_2'],
            ]
        else:
            data = []

        # remove unnecessary data
        for block in data:
            for i in reversed(range(len(block))):
                block_len = len(block[i])
                if block_len == 0:
                    # no data, so remove
                    del block[i]
                elif block_len == 1:
                    # collapse the sub-list for single-column data sets
                    block[i] = block[i][0]
        # block

        # verwijder baan nummers en het kopje "Bronzen finale"
        for block in data[1:]:
            for i in reversed(range(len(block))):
                deelnemer = block[i]
                if len(deelnemer) < 8 or deelnemer[0] != '[' or deelnemer[7] != ']':
                    if deelnemer.upper() != 'BYE':
                        del block[i]
            # for
        # for
        return data


# end of file
