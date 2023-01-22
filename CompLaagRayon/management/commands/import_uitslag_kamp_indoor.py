# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import (KampioenschapSporterBoog, DEELNAME_NEE,
                               KAMP_RANK_UNKNOWN, KAMP_RANK_NO_SHOW, KAMP_RANK_RESERVE)
from openpyxl.utils.exceptions import InvalidFileException
import openpyxl
import zipfile


class Command(BaseCommand):
    help = "Importeer uitslag Indoor kampioenschap"

    blad_voorronde = 'Voorronde'
    blad_finales = 'Finale'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.deelnemers = dict()        # [lid_nr] = [KampioenschapSporterBoog, ...]
        self.dryrun = True

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('bestand', type=str,
                            help='Pad naar het Excel bestand')

    def deelnemers_ophalen(self):
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand='18')
                          .select_related('kampioenschap',
                                          'kampioenschap__nhb_rayon',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'indiv_klasse')):

            # print(deelnemer, deelnemer.indiv_klasse)
            lid_nr = deelnemer.sporterboog.sporter.lid_nr
            try:
                self.deelnemers[lid_nr].append(deelnemer)
            except KeyError:
                self.deelnemers[lid_nr] = [deelnemer]
        # for

    def _importeer_resultaten(self, ws):
        col_lid_nr = 'D'
        col_score1 = 'J'
        col_score2 = 'K'
        col_result = 'Q'

        klasse_pk = None
        deelkamp_pk = None

        # doorloop alle regels van het excel blad en ga op zoek naar bondsnummers
        row_nr = 4
        nix_count = 0
        while nix_count < 10:
            row_nr += 1
            row = str(row_nr)

            lid_nr_str = ws[col_lid_nr + row].value
            if lid_nr_str:
                nix_count = 0
                try:
                    lid_nr = int(lid_nr_str)
                except ValueError:
                    pass
                else:
                    try:
                        deelnemers = self.deelnemers[lid_nr]
                    except KeyError:
                        self.stderr.write('[ERROR] Geen RK deelnemer op regel %s: %s' % (row, lid_nr))
                    else:
                        if len(deelnemers) == 1:
                            deelnemer = deelnemers[0]
                        else:
                            deelnemer = None
                            if klasse_pk:
                                for kandidaat in deelnemers:
                                    if kandidaat.indiv_klasse.pk == klasse_pk:
                                        deelnemer = kandidaat
                                # for
                            if deelnemer is None:
                                # probeer het nog een keer, maar kijk nu ook naar afgemeld status
                                for kandidaat in deelnemers:
                                    if kandidaat.deelname != DEELNAME_NEE:
                                        deelnemer = kandidaat
                                # for
                        if deelnemer is None:
                            self.stderr.write('[ERROR] Kan deelnemer niet bepalen voor regel %s. Keuze uit %s' % (
                                                row, repr(deelnemers)))
                            continue    # met de while

                        dupe_check = False
                        if deelnemer.result_rank > 0:
                            dupe_check = True

                        if klasse_pk != deelnemer.indiv_klasse.pk:
                            if klasse_pk:
                                self.stderr.write('[ERROR] Deelnemer %s hoort in klasse: %s' % (
                                                    deelnemer, deelnemer.indiv_klasse))
                            else:
                                klasse_pk = deelnemer.indiv_klasse.pk
                                deelkamp_pk = deelnemer.kampioenschap.pk
                                self.stdout.write('[INFO] Klasse: %s' % deelnemer.indiv_klasse)

                        score1 = ws[col_score1 + row].value
                        score2 = ws[col_score2 + row].value
                        result = ws[col_result + row].value

                        try:
                            score1 = int(score1)
                            score2 = int(score2)
                        except (TypeError, ValueError):
                            # if deelnemer.deelname != DEELNAME_NEE:      # afgemeld?
                            if score1 is None and score2 is None:
                                self.stdout.write('[WARNING] Regel %s wordt overgeslagen (geen scores)' % row)
                            else:
                                self.stderr.write('[ERROR] Probleem met scores op regel %s: %s en %s' % (
                                                    row, repr(score1), repr(score2)))
                        else:
                            totaal = score1 + score2
                            if totaal > 0:                  # soms wordt 0,0 ingevuld bij niet aanwezig
                                if result and len(str(result)) > 1:
                                    # dit is de rayonkampioen
                                    rank = 1
                                else:
                                    # wel meegedaan, maar met het huidige RK programma weten we niet genoeg
                                    rank = KAMP_RANK_UNKNOWN

                                self.stdout.write('%s: %s, scores: %s %s, result: %s' % (
                                                    rank, deelnemer, score1, score2, result))

                                do_report = False
                                if dupe_check:
                                    # allow result_rank change
                                    is_dupe = (deelnemer.result_score_1 == score1
                                               and deelnemer.result_score_2 == score2)
                                    if not is_dupe:
                                        do_report = True

                                if do_report:
                                    self.stderr.write('[ERROR] Deelnemer pk=%s heeft al andere resultaten! (%s)' % (
                                                        deelnemer.pk, deelnemer))
                                else:
                                    deelnemer.result_rank = rank
                                    deelnemer.result_score_1 = score1
                                    deelnemer.result_score_2 = score2

                        if not self.dryrun:
                            deelnemer.save(update_fields=['result_rank', 'result_score_1', 'result_score_2'])

                        self.deelnemers[lid_nr] = [deelnemer]
            else:
                nix_count += 1
        # while

        # zet deelnemers die niet meegedaan hebben op een hoog rank nummer
        for deelnemers in self.deelnemers.values():
            for deelnemer in deelnemers:
                if deelnemer.kampioenschap.pk == deelkamp_pk and deelnemer.indiv_klasse.pk == klasse_pk:
                    if deelnemer.result_rank in (0, KAMP_RANK_NO_SHOW, KAMP_RANK_RESERVE):
                        if deelnemer.deelname != DEELNAME_NEE:
                            # noteer: we weten niet welke reserves opgeroepen waren
                            # noteer: nog geen oplossing voor reserves die toch niet mee kunnen doen
                            self.stdout.write('[WARNING] Mogelijke no-show voor deelnemer %s' % deelnemer)
                            deelnemer.result_rank = KAMP_RANK_NO_SHOW
                        else:
                            deelnemer.result_rank = KAMP_RANK_RESERVE
                        deelnemer.save(update_fields=['result_rank'])
            # for
        # for

    def _importeer_finales(self, ws):
        # geblokkeerd omdat bronzen finale er niet structureel in zit
        pass

    def handle(self, *args, **options):

        self.dryrun = options['dryrun']

        # open de kopie, zodat we die aan kunnen passen
        fname = options['bestand']
        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))
        try:
            prg = openpyxl.load_workbook(fname,
                                         data_only=True)  # do not evaluate formulas; use last calculated values
        except (OSError, zipfile.BadZipFile, KeyError, InvalidFileException) as exc:
            self.stderr.write('[ERROR] Kan het excel bestand niet openen (%s)' % str(exc))
            return

        try:
            ws_voorronde = prg[self.blad_voorronde]
        except KeyError:
            self.stderr.write('[ERROR] Kan blad %s niet vinden' % repr(self.blad_voorronde))
            return

        try:
            ws_finale = prg[self.blad_finales]
        except KeyError:
            self.stderr.write('[ERROR] Kan blad %s niet vinden' % repr(self.blad_finale))
            return

        self.deelnemers_ophalen()
        self._importeer_resultaten(ws_voorronde)
        self._importeer_finales(ws_finale)


# end of file
