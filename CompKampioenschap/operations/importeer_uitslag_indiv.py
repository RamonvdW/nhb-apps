# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import OutputWrapper
from Competitie.models import Kampioenschap, CompetitieIndivKlasse, KampioenschapSporterBoog
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations.wedstrijdformulieren_indiv_lees import LeesIndivWedstrijdFormulier
from GoogleDrive.operations import StorageGoogleSheet
import io


class ImporteerSheetUitslagIndiv:

    """
        Lees de uitslag uit een Google Sheet
    """

    def __init__(self, deelkamp: Kampioenschap, indiv_klasse: CompetitieIndivKlasse):
        self.bevat_fout = False
        self.blokjes_info = list()
        self.deelkamp = deelkamp
        self.indiv_klasse = indiv_klasse
        self.afstand = 0

        self._data_deelnemers = list()
        self._data_voorronde_uitslag = list()
        self._data_finales = list()

        self._lid_nr2deelnemer = dict()  # [str(lid_nr)] = KampioenschapSporterBoog
        self._lid_nr2voorronde = dict()  # [str(lid_nr)] = score voorronde
        self._lid_nr2rank = dict()       # [str(lid_nr)] = int (1..23)

    def _check_deelnemers(self):
        """ controleer dat iedereen die in de uitslag staat ook op de deelnemerslijst stond
            bepaal aan de hand van het lid_nr en gemiddelde welke deelnemer we moeten hebben.

            vult in: self._lid_nr2deelnemer
        """
        deelnemers = dict()     # [lid_nr] = [KampioenschapSporterBoog, ...]
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=self.deelkamp,
                                  indiv_klasse=self.indiv_klasse)
                          .select_related('sporterboog',
                                          'sporterboog__boogtype',
                                          'sporterboog__sporter',
                                          'indiv_klasse')):

            deelnemer.ag_str = ('%.3f' % deelnemer.gemiddelde).replace('.', ',')
            lid_nr = str(deelnemer.sporterboog.sporter.lid_nr)
            deelnemers[lid_nr] = deelnemer
        # for

        regels_deelnemers = [
            'Gevonden deelnemers:'
        ]

        for row in self._data_deelnemers:
            if len(row) == 0:
                # skip empty row
                continue

            if len(row) != 6:
                regels = [
                    'Fout: Kreeg %s kolommen in plaats van 6' % len(row),
                    'row = %s' % repr(row)
                ]
                self.blokjes_info.append(regels)
                self.bevat_fout = True
                return

            lid_nr, naam, ver, _regio_nr, _label, ag_str = row
            deelnemer = deelnemers.get(lid_nr, None)
            if not deelnemer:
                regels = [
                    'Fout: Deelnemer in de uitslag niet gevonden op de deelnemerslijst!',
                    '[%s] %s' % (lid_nr, naam),
                    'van vereniging %s' % ver
                ]
                self.blokjes_info.append(regels)
                self.bevat_fout = True
            else:
                # geen gemiddelde check
                self._lid_nr2deelnemer[lid_nr] = deelnemer
                regel = "[%s] %s met %s en gemiddelde %s van vereniging %s" % (
                                lid_nr, naam,
                                deelnemer.sporterboog.boogtype.beschrijving,
                                deelnemer.gemiddelde, ver)
                regels_deelnemers.append(regel)
        # for

        self.blokjes_info.append(regels_deelnemers)

    def _bepaal_volgorde_voorronde(self):
        uitslag = list()
        for row, score in zip(self._data_deelnemers, self._data_voorronde_uitslag):
            if len(row) > 0:
                lid_nr = row[0]
                tup = (score, lid_nr)
                uitslag.append(tup)
        # for
        uitslag.sort(reverse=True)      # hoogste eerst

        regels = [
            'Ranking uit voorronde:'
        ]
        for i, tup in enumerate(uitslag):
            score, lid_nr = tup
            if score == 0:
                rank = 99
            else:
                rank = i + 1
            self._lid_nr2rank[lid_nr] = rank
            regel = '%s: %s %s' % (rank, score, lid_nr)
            regels.append(regel)
        # for
        self.blokjes_info.append(regels)

    def lees_sheet(self, bestand):
        """
            Probeert het Google Sheet in te lezen
            Vult in:
                self.afstand
                self._data_deelnemers
                self._data_voorronde_uitslag
                self._data_finales
                self._lid_nr2deelnemer

            Caller moet self.fouten controleren.
        """
        self.afstand = bestand.afstand

        stdout = OutputWrapper(io.StringIO())
        sheets = StorageGoogleSheet(stdout)
        lezer = LeesIndivWedstrijdFormulier(stdout, bestand, sheets)

        foutmeldingen = stdout.getvalue().strip()
        if len(foutmeldingen) > 0:
            regels = foutmeldingen.split('\n')
            regel = 'Fout: inlezen van Google Sheet is niet gelukt'
            regels.insert(0, regel)
            self.blokjes_info.append(regels)
            self.bevat_fout = True
            return

        self._data_deelnemers = lezer.get_indiv_deelnemers()
        self._check_deelnemers()
        if self.bevat_fout:
            return

        self._data_voorronde_uitslag = lezer.get_indiv_voorronde_uitslag()

        if self.afstand == 18:
            # indoor heeft finales
            self._data_finales = lezer.get_indiv_finales_uitslag()
            regels = ['Indoor finales zijn gelezen van blad "Finales %s"' % lezer.finales_blad]
            for data in self._data_finales:
                regels.append('[DEBUG] %s' % ", ".join(data))
            # for
            self.blokjes_info.append(regels)

    @staticmethod
    def _extract_lid_nr(deelnemer) -> str | None:
        # vertaal "[123456] naam" naar "123456"
        if deelnemer[0] == '[' and deelnemer[7] == ']':
            return deelnemer[1:1+6]
        return None

    def _uitslag2rank(self, uitslag):
        if uitslag == '4e':
            return 4
        if uitslag == 'Brons':
            return 3
        if uitslag == 'Zilver':
            return 2
        if uitslag.startswith('Goud'):
            return 1

        regels = [
            'Kan rank niet bepalen uit uitslag beschrijving %s' % repr(uitslag)
        ]
        self.blokjes_info.append(regels)
        self.bevat_fout = True
        return 0

    def _bepaal_uitslag_18(self):
        lid_nrs_done = list()

        # begin bij de medailles
        uitslag = self._data_finales[0]
        finalisten = self._data_finales[1]
        if len(uitslag) != len(finalisten):
            regels = [
                'Fout: data van de medaille finales is niet compleet',
                'Uitslag: %s' % repr(uitslag),
                'Finalisten: %s' % repr(finalisten)
            ]
            self.blokjes_info.append(regels)
            self.bevat_fout = True
            return

        regels = ['Ranking uit de medaille finales:']
        for i in range(len(uitslag)):
            lid_nr = self._extract_lid_nr(finalisten[i])
            if lid_nr:
                rank = self._uitslag2rank(uitslag[i])
                self._lid_nr2rank[lid_nr] = rank
                lid_nrs_done.append(lid_nr)
                regel = '%s: %s' % (rank, lid_nr)
                regels.append(regel)
            else:
                regel = 'Finalist %s wordt overgeslagen' % repr(finalisten[i])
                regels.append(regel)
        # for
        self.blokjes_info.append(regels)

        # ga verder met de 1/4 finales (laatste 8)
        for data in self._data_finales[3:]:
            regels = ['Ranking uit de voorgaande finale ronde:']
            rank = len(lid_nrs_done) + 1
            aantal = 0
            for deelnemer in data:
                lid_nr = self._extract_lid_nr(deelnemer)
                if lid_nr:
                    if lid_nr not in lid_nrs_done:
                        self._lid_nr2rank[lid_nr] = rank
                        lid_nrs_done.append(lid_nr)
                        aantal += 1
                        regel = '%s: %s' % (rank, lid_nr)
                        regels.append(regel)
                else:
                    regel = 'Finalist %s wordt overgeslagen' % repr(deelnemer)
                    regels.append(regel)
            # for

            if (rank == 5 and aantal > 4) or (rank == 9 and aantal > 8):
                regels.append('Fout: te veel sporters met rank %s' % rank)
                self.bevat_fout = True

            self.blokjes_info.append(regels)
        # for

        regels = ['Uitslag:']
        uitslag = list()
        for lid_nr, rank in self._lid_nr2rank.items():
            tup = (rank, lid_nr)
            uitslag.append(tup)
        # for
        uitslag.sort()
        for rank, lid_nr in uitslag:
            regel = '%s: %s' % (rank, lid_nr)
            regels.append(regel)
        # for
        self.blokjes_info.append(regels)

    def _bepaal_uitslag_25(self):
        regels = ['Fout: 25m1pijl is nog niet ondersteund']
        self.blokjes_info.append(regels)
        self.bevat_fout = True

    def bepaal_uitslag(self):
        self._bepaal_volgorde_voorronde()

        if self.afstand == 18:
            self._bepaal_uitslag_18()
        else:
            self._bepaal_uitslag_25()

    def uitslag_opslaan(self):
        pass


def importeer_sheet_uitslag_indiv(deelkamp: Kampioenschap, klasse: CompetitieIndivKlasse, status: SheetStatus) -> tuple[bool, list[str]]:
    """
        Lees de uitslag uit een Google Sheet en sla deze op in de database

        Return values:
            bevat_fout:
                True als er problemen zijn. Details in blokjes_info
                False als alles goed is. Informatie in blokjes_info

            blokjes_info: [
                             # blokje1
                             [
                                 str,
                                 str,
                                 ..
                             ],
                             # blokje2
                             ...
                         ]
    """

    imp = ImporteerSheetUitslagIndiv(deelkamp, klasse)
    imp.lees_sheet(status.bestand)

    if not imp.bevat_fout:
        # geen fouten, ga door met importeren
        imp.bepaal_uitslag()

    if not imp.bevat_fout:
        # geen fouten, dus publiceer de uitslag
        imp.uitslag_opslaan()

    return imp.bevat_fout, imp.blokjes_info


# end of file
