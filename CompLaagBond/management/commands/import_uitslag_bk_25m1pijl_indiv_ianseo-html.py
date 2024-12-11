# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK, DEELNAME_NEE, KAMP_RANK_NO_SHOW, KAMP_RANK_RESERVE
from Competitie.models import KampioenschapSporterBoog


class Command(BaseCommand):
    help = "Importeer uitslag 25m1pijl BK individueel uit Ianseo download"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.ver2deelnemers = dict()     # [ver_nr] = [KampioenschapSporterBoog, ...]
        self.klasse_pk = None
        self.dryrun = True
        self.verbose = False

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('bestand', type=str,
                            help='Pad naar het HTML bestand')

    def deelnemers_ophalen(self):
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand='25',
                                  kampioenschap__deel=DEEL_BK)
                          .select_related('kampioenschap',
                                          'sporterboog__sporter',
                                          'sporterboog__boogtype',
                                          'bij_vereniging',
                                          'indiv_klasse')):

            ver_nr = deelnemer.bij_vereniging.ver_nr
            try:
                self.ver2deelnemers[ver_nr].append(deelnemer)
            except KeyError:
                self.ver2deelnemers[ver_nr] = [deelnemer]
        # for

    def _read_html(self, fname):
        self.stdout.write('[INFO] Lees bestand %s' % repr(fname))
        try:
            with open(fname) as f:
                data = f.read()
        except OSError as exc:
            self.stderr.write('[ERROR] Kan het html bestand niet openen (%s)' % str(exc))
            return

        rank_doorlopend = 0
        rank_deze = 0
        prev_totaal = 0
        prev_counts_str = ''
        toon_counts = True
        klasse_titel = ''
        tabel = data[data.find('<table'):data.find('</table>')]
        for regel in tabel.split('</tr>'):
            if '</td>' in regel:
                parts = list()
                for part in regel.split('</td>'):
                    pos = part.rfind('>')
                    parts.append(part[pos + 1:])
                # for
                if len(parts) == 9:
                    # print('data: %s' % repr(parts))
                    rank, naam, ver, score1, score2, _, count10, count9, _ = parts
                    ver = ver[:4]
                    if self.verbose:
                        self.stdout.write('   %s %s %s %s %s %s %s' % (
                            rank, ver, naam, score1, score2, count10, count9))

                    ver_nr = int(ver)
                    score1 += '/'
                    score1 = int(score1[:score1.find('/')])
                    score2 += '/'
                    score2 = int(score2[:score2.find('/')])
                    count10 = int(count10)
                    count9 = int(count9)
                    totaal = score1 + score2

                    matches = list()
                    up_naam = naam.upper()
                    for deelnemer in self.ver2deelnemers[ver_nr]:
                        sporter = deelnemer.sporterboog.sporter
                        if sporter.voornaam.upper() in up_naam:
                            # warm
                            match = 3

                            # achternaam kan gehusseld zijn, dus kijk per woord
                            for part in sporter.achternaam.upper().split(' '):
                                if part in up_naam:
                                    match += 2
                                    # print('match: %s' % repr(part))
                            # for

                            if deelnemer.sporterboog.boogtype.beschrijving in klasse_titel:
                                match += 10

                            tup = (match, deelnemer.pk, deelnemer)
                            matches.append(tup)
                    # for

                    if len(matches) == 0:
                        self.stderr.write('[WARNING] Deelnemer %s niet gevonden!' % (repr(naam)))
                        for deelnemer in self.ver2deelnemers[ver_nr]:
                            self.stdout.write('[INFO] kandidaat? %s' % deelnemer)
                        # for
                    else:
                        matches.sort(reverse=True)      # hoogste eerst
                        # for match, _, deelnemer in matches:
                        #     print('   kandidaat: (match %s): %s' % (match, deelnemer))
                        _, _, deelnemer = matches[0]
                        # print(' deelnemer: %s' % deelnemer)

                        counts_str = "%sx10, %sx9" % (count10, count9)

                        rank_doorlopend += 1

                        # print('rank_doorlopend=%s, totaal=%s, prev_totaal=%s, counts_str=%s, prev_counts_str=%s' % (
                        #           rank_doorlopend, totaal, prev_totaal, counts_str, prev_counts_str))

                        if totaal == prev_totaal:
                            if rank_deze > 3:
                                # we kijken niet meer naar counts_str
                                # zelfde totaal = zelfde rank
                                if self.verbose:
                                    self.stdout.write('[INFO] Zelfde score: %s == %s' % (totaal, prev_totaal))

                            elif counts_str == prev_counts_str:
                                # zelfde score --> zelf rank
                                if self.verbose:
                                    self.stdout.write('[INFO] Zelfde score: %s == %s en counts: %s == %s' % (
                                                        totaal, prev_totaal, counts_str, prev_counts_str))
                            else:
                                rank_deze = rank_doorlopend

                        elif totaal > prev_totaal and rank_doorlopend > 1:
                            self.stderr.write('[ERROR] Score is niet aflopend')

                        else:
                            # geef rank
                            rank_deze = rank_doorlopend

                        # counts worden alleen gebruikt voor plaats 1, 2, 3
                        # nog wel tonen voor plaats 3+ als deze relevant was
                        if rank_deze > 3 and totaal != prev_totaal:
                            toon_counts = False

                        if not toon_counts:
                            counts_str = ''

                        prev_totaal = totaal
                        prev_counts_str = counts_str

                        if rank == 'DNS':
                            deelnemer.result_rank = KAMP_RANK_NO_SHOW
                            deelnemer.result_volgorde = 99
                            deelnemer.result_score_1 = 0
                            deelnemer.result_score_2 = 0
                            deelnemer.result_counts = ''
                        else:
                            if str(rank_deze) != rank:
                                self.stdout.write('[WARNING] Afwijkende rank: %s vs %s' % (rank_deze, rank))

                            deelnemer.result_rank = rank_deze
                            deelnemer.result_volgorde = rank_doorlopend
                            deelnemer.result_score_1 = score1
                            deelnemer.result_score_2 = score2
                            deelnemer.result_counts = counts_str

                        if not self.dryrun:
                            deelnemer.save(update_fields=['result_rank', 'result_volgorde',
                                                          'result_score_1', 'result_score_2', 'result_counts'])

            else:
                parts = list()
                for part in regel.split('</th>'):
                    pos = part.rfind('>')
                    parts.append(part[pos + 1:])
                # for
                # print('header: %s' % repr(parts))
                header = parts[0]
                if len(header) > 10:
                    self.stdout.write('[INFO] Klasse: %s' % repr(header))
                    klasse_titel = header
                    rank_doorlopend = rank_deze = 0
                    prev_totaal = 0
                    prev_counts_str = ''
                    toon_counts = True
        # for

        # zet deelnemers die niet meegedaan hebben op een hoog rank nummer
        for ver, deelnemers in self.ver2deelnemers.items():
            for deelnemer in deelnemers:
                if deelnemer.result_rank in (0, KAMP_RANK_NO_SHOW, KAMP_RANK_RESERVE):
                    if deelnemer.deelname != DEELNAME_NEE:
                        # noteer: we weten niet welke reserves opgeroepen waren
                        # noteer: nog geen oplossing voor reserves die toch niet mee kunnen doen
                        if self.verbose:
                            self.stdout.write('[WARNING] Mogelijke no-show voor deelnemer %s' % deelnemer)
                        deelnemer.result_rank = KAMP_RANK_NO_SHOW
                        deelnemer.result_volgorde = 99
                    else:
                        deelnemer.result_rank = KAMP_RANK_RESERVE
                        deelnemer.result_volgorde = 99

                    if not self.dryrun:
                        deelnemer.save(update_fields=['result_rank', 'result_volgorde'])
            # for
        # for

    def handle(self, *args, **options):

        self.dryrun = options['dryrun']
        self.verbose = options['verbose']
        fname = options['bestand']

        self.deelnemers_ophalen()

        self._read_html(fname)


# end of file
