# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_BK
from Competitie.models import KampioenschapSporterBoog
import pypdf


class LeesPdf(object):

    def __init__(self, start_at="", stop_at=""):
        self.start_at = start_at
        self.stop_at = stop_at

        self.found_start = False
        self.found_stop = False

        self.huidige_regel = list()
        self.regels = list()

    def _visitor(self, text, cm, tm, font_dict, font_size):     # noqa
        """ Deze functie wordt aangeroepen vanuit de PdfReader om information uit een stukje tekst te halen """
        if self.found_stop:
            return

        if not text:
            # skip lege regel
            return

        # print(self.found_start, repr(text))
        if self.stop_at in text:
            self.found_stop = True
            return

        if text == '\n':
            if self.found_start:
                self.regels.append(self.huidige_regel)
            else:
                if self.start_at in " ".join(self.huidige_regel):
                    self.found_start = True

            self.huidige_regel = list()
        else:
            self.huidige_regel.append(text.strip())

    def extract_from_pdf(self, fpath):
        self.found_start = False
        self.found_stop = False

        reader = pypdf.PdfReader(fpath)
        for page in reader.pages:
            page.extract_text(visitor_text=self._visitor)
            if self.found_stop:
                break
        # for

        if len(self.huidige_regel):
            self.regels.append(self.huidige_regel)
            self.huidige_regel = list()

        lst = list()

        for regel in self.regels:
            # print('(%s) %s' % (len(regel), repr(regel)))

            # verwachte kolommen:
            #   pos, baan, naam, klasse, ver_nr, ver_naam, score1/rank, score2/rank, totaal, aantal-10, aantal-9
            if len(regel) >= 11:
                _, _, naam, _, ver_nr, _, score1, score2, _, count10, count9 = regel[:11]

                pos1 = score1.find('/')
                pos2 = score2.find('/')
                if pos1 > 0:
                    score1 = score1[:pos1]
                if pos2 > 0:
                    score2 = score2[:pos2]
                score1 = int(score1)
                score2 = int(score2)
                count10 = int(count10)
                count9 = int(count9)
                ver_nr = int(ver_nr)

                tup = (naam, ver_nr, score1, score2, count10, count9)
                lst.append(tup)
        # for

        return lst


class Command(BaseCommand):
    help = "Importeer uitslag team kampioenschap 25m1pijl Ianseo pdf"

    # PDF moet individuele bijdrage aan de teams bevatten
    # kolommen: Pos, Baan, Naam, VerNr++, Team naam, Score1/rank, Score2/rank, aantal 10, aantal 9

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.dryrun = True
        self.verbose = False
        self.deelnemers = dict()            # [NAAM VOOR ACHTER | NAAM ACHTER VOOR] = [KampioenschapSporterBoog, ...]
        self.indiv_klasse = None
        self.uitslag = list()

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')
        parser.add_argument('bestand', type=str,
                            help='Pad naar het pdf bestand')

    def _deelnemers_ophalen(self):
        # alle deelnemers van de RK individueel mogen meedoen met de BK teams
        # daarom halen we de DEEL_RK sporters op
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap__competitie__afstand='25',
                                  kampioenschap__deel=DEEL_BK)
                          .select_related('kampioenschap',
                                          'sporterboog__sporter',
                                          'indiv_klasse')):

            sporter = deelnemer.sporterboog.sporter
            voor = sporter.voornaam.upper()
            achter = sporter.achternaam.upper()
            key1 = voor + ' ' + achter
            key2 = achter + ' ' + voor
            key3 = key2.split()
            key3.sort()
            key3 = " ".join(key3)

            for key in (key1, key2):
                try:
                    self.deelnemers[key].append(deelnemer)
                except KeyError:
                    self.deelnemers[key] = [deelnemer]
            # for

            if key3 not in (key1, key2):
                try:
                    self.deelnemers[key3].append(deelnemer)
                except KeyError:
                    self.deelnemers[key3] = [deelnemer]
        # for

    def _bepaal_klasse(self, regels):
        """ zoek uit (met een majority vote) welke klasse dit zou moeten zijn """

        pk2klasse = dict()          # [klasse.pk] = klasse
        klasse2count = dict()       # [klasse.pk] = count

        for regel in regels:
            # print('regel: %s' % repr(regel))
            naam = regel[0]
            key = naam.upper()
            try:
                deelnemers = self.deelnemers[key]
            except KeyError:
                key3 = key.split()
                key3.sort()
                key3 = " ".join(key3)
                try:
                    deelnemers = self.deelnemers[key3]
                except KeyError:
                    self.stdout.write('[WARNING] Kan deelnemer %s niet vinden' % repr(key))
                    deelnemers = list()

            for deelnemer in deelnemers:
                klasse = deelnemer.indiv_klasse
                pk2klasse[klasse.pk] = klasse
                try:
                    klasse2count[klasse.pk] += 1
                except KeyError:
                    klasse2count[klasse.pk] = 1
            # for
        # for

        top_klasse = None
        hoogste = 0
        for pk, count in klasse2count.items():
            if count > hoogste:
                hoogste = count
                top_klasse = pk2klasse[pk]
        # for

        if not top_klasse:
            self.stderr.write('[ERROR] Kan team klasse niet bepalen (0 matches op team naam)')
        else:
            self.stdout.write('[INFO] Individuele klasse: %s' % top_klasse.beschrijving)

        self.indiv_klasse = top_klasse

    def _bepaal_deelnemer(self, naam, ver_nr):
        """ zoek een KampioenschapSporterBoog die het beste bij de naam van de sporter past """

        try:
            deelnemers = self.deelnemers[naam.upper()]
        except KeyError:
            key3 = naam.upper().split()
            key3.sort()
            key3 = " ".join(key3)
            deelnemers = self.deelnemers[key3]

        deelnemers = [deelnemer
                      for deelnemer in deelnemers
                      if deelnemer.sporterboog.boogtype == self.indiv_klasse.boogtype]

        if len(deelnemers) != 1:
            self.stderr.write('[ERROR] Kan deelnemer %s niet bepalen. Opties: %s' % (repr(naam), repr(deelnemers)))
            return None

        deelnemer = deelnemers[0]
        self.stdout.write('[INFO] Gevonden deelnemer: %s' % deelnemer)

        if deelnemer.bij_vereniging.ver_nr != ver_nr:
            self.stderr.write('[WARNING] Deelnemer pk=%s heeft vereniging %s maar uitslag zegt %s' % (
                        deelnemer.pk,
                        deelnemer.sporterboog.sporter.bij_vereniging.ver_nr,
                        ver_nr))

        return deelnemer

    def _verwerk_uitslag(self, regels):
        """ verwerk de regels die uit de PDF gehaald
            en maak er een uitslag van """

        self._bepaal_klasse(regels)
        if not self.indiv_klasse:
            return

        uitslag = list()
        regel_nr = 0
        for regel in regels:
            regel_nr += 1
            naam, ver_nr, score1, score2, count10, count9 = regel
            if self.verbose:
                self.stdout.write('[INFO] Data in: %s %s %s %s %s %s' % (
                                    repr(naam), repr(ver_nr), score1, score2, count10, count9))

            totaal = score1 + score2
            if totaal > 0:
                deelnemer = self._bepaal_deelnemer(naam, ver_nr)
                if deelnemer:
                    deelnemer.result_score_1 = score1
                    deelnemer.result_score_2 = score2

                    counts = list()
                    if count10:
                        counts.append('%sx10' % count10)
                    if count9:
                        counts.append('%sx9' % count9)
                    counts_str = ", ".join(counts)
                    deelnemer.result_counts = counts_str

                    tup = (totaal, count10, count9, 0-regel_nr, deelnemer)
                    uitslag.append(tup)
        # for

        # bepaal de uitslag
        uitslag.sort(reverse=True)      # hoogste eerst
        self.stdout.write('Uitslag:')
        if self.verbose:
            for tup in uitslag:
                self.stdout.write('%s' % repr(tup))
            # for

        rank = 0
        rank_doorlopend = 0
        prev_totaal = -1
        prev_count10 = -1
        prev_count9 = -1
        toon_counts = True
        for totaal, count10, count9, _, deelnemer in uitslag:
            rank_doorlopend += 1

            # zelfde score, zelf rank
            zelfde_score = True
            if totaal != prev_totaal:
                zelfde_score = False
            else:
                if toon_counts:
                    # vergelijk ook de counts
                    if count10 != prev_count10 or count9 != prev_count9:
                        zelfde_score = False

            if not zelfde_score:
                rank = rank_doorlopend

            deelnemer.result_rank = rank
            deelnemer.result_volgorde = rank_doorlopend

            # counts worden alleen gebruikt voor plaats 1, 2, 3
            # nog wel tonen voor plaats 3+ als deze relevant was
            if rank > 3 and totaal != prev_totaal:
                toon_counts = False

            prev_totaal, prev_count10, prev_count9 = totaal, count10, count9

            if not toon_counts:
                deelnemer.result_counts = ''

            self.stdout.write('  %s %s %s %s' % (
                rank,
                totaal,
                deelnemer.result_counts,
                deelnemer.sporterboog.sporter.lid_nr_en_volledige_naam()))

            if not self.dryrun:
                deelnemer.save(update_fields=['result_rank', 'result_volgorde',
                                              'result_score_1', 'result_score_2', 'result_counts'])

            self.uitslag.append(deelnemer)
        # for

    def _verwijder_onnodige_result_counts(self):
        aantal = len(self.uitslag)
        prev_totaal = None
        for nr in range(aantal):
            deelnemer = self.uitslag[nr]
            totaal = deelnemer.result_score_1 + deelnemer.result_score_2

            if deelnemer.result_counts:
                keep_counts_due_to_prev = (totaal == prev_totaal)
                if nr < aantal - 1:
                    next_deelnemer = self.uitslag[nr+1]
                    next_totaal = next_deelnemer.result_score_1 + next_deelnemer.result_score_2
                    keep_counts_due_to_next = (totaal == next_totaal)
                else:
                    keep_counts_due_to_next = False

                if deelnemer.result_counts:
                    if not (keep_counts_due_to_prev or keep_counts_due_to_next):
                        deelnemer.result_counts = ''
                        deelnemer.save(update_fields=['result_counts'])

            prev_totaal = totaal
        # for

    def handle(self, *args, **options):

        self.dryrun = options['dryrun']
        self.verbose = options['verbose']

        # open de kopie, zodat we die aan kunnen passen
        fpath = options['bestand']
        self.stdout.write('[INFO] Lees bestand %s' % repr(fpath))
        lees = LeesPdf(start_at="Na 50 pijlen", stop_at="Shoot Off")
        try:
            regels = lees.extract_from_pdf(fpath)
        except FileNotFoundError:
            self.stderr.write('[ERROR] Kan bestand niet vinden')
            return
        del lees

        self._deelnemers_ophalen()
        self._verwerk_uitslag(regels)
        self._verwijder_onnodige_result_counts()

# end of file
