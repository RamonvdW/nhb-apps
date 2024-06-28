# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK
from Competitie.models import Kampioenschap, KampioenschapSporterBoog, KampioenschapIndivKlasseLimiet


class Command(BaseCommand):
    help = "Controleer rank, volgorde en gemiddelde in BK deelnemerslijst"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.verbose = False
        self.count_ok = 0

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'),
                            help='Competitie afstand (18/25)')
        parser.add_argument('--verbose', action='store_true')

    def _out_block(self, block):
        if len(block) < 1:
            return

        if not self.verbose:
            # alleen tonen als het nuttig is
            has_error = any('[ERROR]' in line for line in block)
            if not has_error:
                self.count_ok += 1
                # group = block.pop(0)
                # self.stdout.write(group)
                # self.stdout.write('[INFO] Geen afwijkingen')
                return

        for line in block:
            if line.startswith('[ERROR]'):
                self.stderr.write(line)
            else:
                self.stdout.write(line)
        # for
        self.stdout.write('')

    def handle(self, *args, **options):

        afstand = options['afstand']
        self.verbose = options['verbose']

        try:
            kampioenschap = Kampioenschap.objects.get(competitie__afstand=afstand, deel=DEEL_BK)
        except Kampioenschap.DoesNotExist:
            self.stderr.write('[ERROR] BK niet gevonden')
            return

        klasse_pk2limiet = dict()       # [indiv_klasse.pk] = limiet
        for limiet in KampioenschapIndivKlasseLimiet.objects.filter(kampioenschap=kampioenschap):
            klasse_pk2limiet[limiet.indiv_klasse.pk] = limiet.limiet
        # for

        sporterboog_pks = list()
        prev_klasse = -1
        prev_volgorde = 0
        prev_gemiddelde = 0
        prev_rank = 0
        net_na_cut = False
        limiet = 0
        block = list()

        for kampioen in (KampioenschapSporterBoog
                         .objects
                         .filter(kampioenschap=kampioenschap)
                         .select_related('sporterboog',
                                         'sporterboog__sporter',
                                         'sporterboog__boogtype',
                                         'indiv_klasse')
                         .order_by('indiv_klasse__volgorde',
                                   'volgorde',
                                   '-gemiddelde')):

            if kampioen.indiv_klasse.volgorde != prev_klasse:
                self._out_block(block)
                block = list()

                prev_klasse = kampioen.indiv_klasse.volgorde
                prev_volgorde = 0
                prev_gemiddelde = 0
                prev_rank = 0

                net_na_cut = False
                try:
                    limiet = klasse_pk2limiet[kampioen.indiv_klasse.pk]
                except KeyError:
                    limiet = 24

                block.append('[INFO] ---------- Indiv klasse: %s (limiet = %s) ----------' % (kampioen.indiv_klasse,
                                                                                              limiet))

            block.append('[INFO] rank %2d, volgorde %3d, gem=%.3f, deelname=%s, sporterboog %s' % (
                                kampioen.rank, kampioen.volgorde, kampioen.gemiddelde,
                                kampioen.deelname, kampioen.sporterboog))

            if kampioen.sporterboog.pk not in sporterboog_pks:
                sporterboog_pks.append(kampioen.sporterboog.pk)
            else:
                block.append('[ERROR] Dubbele sporterboog: %s' % kampioen.sporterboog)

            if prev_volgorde:
                if kampioen.volgorde != prev_volgorde + 1:
                    block.append('[ERROR] Volgorde niet consecutief (pk=%s)' % kampioen.pk)

            prev_volgorde = kampioen.volgorde
            if kampioen.rank:
                if kampioen.rank == limiet:
                    net_na_cut = True

                if prev_rank:
                    if kampioen.rank != prev_rank + 1:
                        block.append('[ERROR] Rank niet consecutief (pk=%s)' % kampioen.pk)

                if prev_rank > 0 and kampioen.gemiddelde > prev_gemiddelde:
                    if not net_na_cut:
                        block.append('[ERROR] Gemiddelde is niet consecutief (pk=%s)' % kampioen.pk)

                prev_rank = kampioen.rank
                prev_gemiddelde = kampioen.gemiddelde
        # for

        self._out_block(block)

        if prev_klasse == -1:
            self.stdout.write('[WARNING] Geen deelnemers gevonden')

        elif self.count_ok > 0:
            self.stdout.write('[INFO] %s klassen hebben geen afwijkingen (gebruik --verbose om alles te zien)' %
                              self.count_ok)

# end of file
