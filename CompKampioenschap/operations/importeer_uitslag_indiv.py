# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.core.management.base import OutputWrapper
from Competitie.definities import KAMP_RANK_NO_SHOW
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
        self._data_voorronde_scores = list()    # list([1e, 2e, totaal, 10en, 9ens, 8en], ...)
        self._data_voorronde_uitslag = list()   # list(125, 124.2, 124.1, ...)
        self._data_finales = list()

        self._lid_nr2deelnemer = dict()         # [str(lid_nr)] = KampioenschapSporterBoog
        self._lid_nr2voorronde = dict()         # [str(lid_nr)] = [totaal, aantallen_str, 1e, 2e]
        self._lid_nr2rank_volgorde = dict()     # [str(lid_nr)] = (rank, volgorde)

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
        """ bepaal de ranking voor elke deelnemer als we naar het voorronde blad kijken

            vult:
                self._lid_nr2rank_volgorde
                self._lid_nr2voorronde
        """
        uitslagen = list()
        for row, uitslag, scores in zip(self._data_deelnemers, self._data_voorronde_uitslag, self._data_voorronde_scores):
            if len(row) > 0:
                lid_nr = row[0]
                tup = (uitslag, lid_nr)
                uitslagen.append(tup)

                scores.extend(['', '', '', '', '', ''])
                score1, score2, score_totaal, c10, c9, c8 = scores[:6]

                # converteer de telling van 10-en, 9-ens en 8-en voor de 25m1pijl
                counts = list()
                try:
                    if c10:
                        c10 = int(c10)
                        counts.append('%sx10' % c10)
                    else:
                        c10 = 0
                    if c9:
                        c9 = int(c9)
                        counts.append('%sx9' % c9)
                    else:
                        c9 = 0
                    if c8:
                        c8 = int(c8)
                        counts.append('%sx8' % c8)
                    else:
                        c8 = 0
                except (TypeError, ValueError) as err:
                    regels = [
                        'Fout: Probleem met 10/9/8 tellingen voor [%s]: %s' % (lid_nr, repr(scores))
                    ]
                    self.blokjes_info.append(regels)
                    self.bevat_fout = True
                    counts_str = ''
                else:
                    if c10 + c9 + c8 > (2 * 25):
                        regels = [
                            'Fout: Te veel 10/9/8-en voor [%s]: %s' % (lid_nr, repr(scores))
                        ]
                        self.blokjes_info.append(regels)
                        self.bevat_fout = True
                    counts_str = " ".join(counts)

                tup = (score_totaal, counts_str, score1, score2)
                self._lid_nr2voorronde[lid_nr] = tup
        # for
        uitslagen.sort(reverse=True)      # hoogste eerst

        regels = [
            'Ranking uit voorronde:'
        ]
        for i, tup in enumerate(uitslagen):
            score, lid_nr = tup
            if score == 0:
                rank = 99
            else:
                rank = i + 1
            self._lid_nr2rank_volgorde[lid_nr] = (rank, rank)
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
        lezer = LeesIndivWedstrijdFormulier(stdout, bestand, sheets, lees_oppervlakkig=False)

        foutmeldingen = stdout.getvalue().strip()
        if len(foutmeldingen) > 0:
            regels = foutmeldingen.split('\n')
            regels = [regel
                      for regel in regels
                      if (regel != '[ERROR] {execute} HttpError from API:'
                          and not regel.startswith('[DEBUG] {execute} Retrying in'))]
            if len(regels) > 0:
                regel = 'Fout: inlezen van Google Sheet is niet gelukt'
                regels.insert(0, regel)
                self.blokjes_info.append(regels)
                self.bevat_fout = True
                return

        self._data_deelnemers = lezer.get_indiv_deelnemers()
        self._check_deelnemers()
        if self.bevat_fout:
            return

        self._data_voorronde_scores = lezer.get_indiv_voorronde_scores()
        self._data_voorronde_uitslag = lezer.get_indiv_voorronde_uitslag()

        # zorg dat de lijsten even lang zijn
        while len(self._data_voorronde_scores) < len(self._data_deelnemers):
            self._data_voorronde_scores.append([0, 0, 0, ''])

        while len(self._data_voorronde_uitslag) < len(self._data_deelnemers):
            self._data_voorronde_uitslag.append(0)

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
        finale_uitslag = self._data_finales[0]
        finale_deelnemers = self._data_finales[1]

        # geen bronzen finale?
        if len(finale_uitslag) == 2 and finale_deelnemers[-2] == 'BYE' and finale_deelnemers[-1] == 'BYE':
            finale_deelnemers = finale_deelnemers[:2]

        if len(finale_uitslag) != len(finale_deelnemers):
            regels = [
                'Fout: data van de medaille finales is niet compleet',
                'Uitslag: %s' % repr(finale_uitslag),
                'Finalisten: %s' % repr(finale_deelnemers)
            ]
            self.blokjes_info.append(regels)
            self.bevat_fout = True
            return

        uitslag = list()

        regels = ['Ranking uit de medaille finales:']
        for i in range(len(finale_uitslag)):
            lid_nr = self._extract_lid_nr(finale_deelnemers[i])
            if lid_nr:
                rank = self._uitslag2rank(finale_uitslag[i])       # vertaalt "Zilver", "Brons", etc. naar 1/2/3/4
                self._lid_nr2rank_volgorde[lid_nr] = (rank, rank)

                scores = self._lid_nr2voorronde[lid_nr]
                tup = (rank, -scores[0], scores, lid_nr)
                uitslag.append(tup)

                lid_nrs_done.append(lid_nr)
                regel = '%s: %s' % (rank, lid_nr)
                regels.append(regel)
            else:
                regel = 'Finalist %s wordt overgeslagen' % repr(finale_deelnemers[i])
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
                        scores = self._lid_nr2voorronde[lid_nr]
                        tup = (rank, -scores[0], scores, lid_nr)
                        uitslag.append(tup)

                        lid_nrs_done.append(lid_nr)
                        regel = '%s: %s' % (rank, lid_nr)
                        regels.append(regel)

                        aantal += 1
                else:
                    regel = 'Finalist %s wordt overgeslagen' % repr(deelnemer)
                    regels.append(regel)
            # for

            if (rank == 5 and aantal > 4) or (rank == 9 and aantal > 8):
                regels.append('Fout: te veel sporters met rank %s' % rank)
                self.bevat_fout = True

            self.blokjes_info.append(regels)
        # for

        uitslag.sort()      # rank 1 eerst, meest negative totaal score eerst

        # vul de volgorde in van de overige deelnemers
        regels = ['Uitslag:']
        volgorde = 0
        for rank, _min, scores, lid_nr in uitslag:
            volgorde += 1
            self._lid_nr2rank_volgorde[lid_nr] = (rank, volgorde)
            totaal, aantal_str, score1, score2 = scores
            regel = '%s #%s [%s] %s (%s+%s) %s' % (rank, volgorde, lid_nr, totaal, score1, score2, aantal_str)
            regels.append(regel)
        # for

        # voeg de deelnemers toe die de finales niet gehaald hebben
        for lid_nr, deelnemer in self._lid_nr2deelnemer.items():
            if lid_nr not in lid_nrs_done:
                if lid_nr not in self._lid_nr2rank_volgorde:
                    self._lid_nr2rank_volgorde[lid_nr] = (99, 99)
                    self._lid_nr2voorronde[lid_nr] = (0, '', 0, 0)

                rank, volgorde = self._lid_nr2rank_volgorde[lid_nr]
                scores = self._lid_nr2voorronde[lid_nr]

                totaal, aantal_str, score1, score2 = scores
                regel = '%s #%s [%s] %s (%s+%s) %s' % (rank, volgorde, lid_nr, totaal, score1, score2, aantal_str)
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
        stamp = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M:%S')

        for lid_nr, deelnemer in self._lid_nr2deelnemer.items():
            rank, volgorde = self._lid_nr2rank_volgorde[lid_nr]
            score_totaal, counts_str, score1, score2 = self._lid_nr2voorronde[lid_nr]

            if rank == 99:
                rank = KAMP_RANK_NO_SHOW
            else:
                if deelnemer.result_score_1 != score1 or deelnemer.result_score_2 != score2 or deelnemer.result_counts != counts_str:
                    deelnemer.logboek += '[%s] Scores bijgewerkt: %s, %s, %s --> %s, %s, %s\n' % (stamp,
                                                                                                  deelnemer.result_score_1,
                                                                                                  deelnemer.result_score_2,
                                                                                                  repr(deelnemer.result_counts),
                                                                                                  score1,
                                                                                                  score2,
                                                                                                  repr(counts_str))
                    deelnemer.result_score_1 = score1
                    deelnemer.result_score_2 = score2
                    deelnemer.result_counts = counts_str

            if deelnemer.result_rank != rank or deelnemer.result_volgorde != volgorde:
                deelnemer.logboek += '[%s] Rank en volgorde bijgewerkt: %s, %s --> %s, %s\n' % (stamp,
                                                                                                deelnemer.result_rank,
                                                                                                deelnemer.result_volgorde,
                                                                                                rank,
                                                                                                volgorde)

                deelnemer.result_rank = rank                # 0 = niet mee gedaan
                deelnemer.result_volgorde = volgorde

            # print(deelnemer.logboek)

            deelnemer.save(update_fields=['result_score_1', 'result_score_2', 'result_counts',
                                          'result_rank', 'result_volgorde',
                                          'logboek'])
        # for


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
