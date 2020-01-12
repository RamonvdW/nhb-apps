# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

import argparse
from django.core.management.base import BaseCommand
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbVereniging


TOEGESTANE_KLASSEN = ('Recurve', 'Compound', 'Barebow', 'Longbow', 'Instinctive Bow')


class Command(BaseCommand):
    help = "Importeer competitie historie"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=argparse.FileType("r"),
                            help="in te lezen file")
        parser.add_argument('seizoen', nargs=1,
                            help="competitie seizoen: 20xx-20yy")
        parser.add_argument('comptype', nargs=1, choices=('18', '25'),
                            help="competitie type: 18 of 25")
        parser.add_argument('--verbose', action='store_true')

    @staticmethod
    def make_or_find_histcompetitie(seizoen, comp_type, klasse):
        # check if the record already exists
        objs = HistCompetitie.objects.filter(
                        seizoen=seizoen,
                        comp_type=comp_type,
                        klasse=klasse,
                        is_team=False)
        if len(objs):
            # return existing object
            histcompetitie = objs[0]
        else:
            # create new object
            histcompetitie = HistCompetitie()
            histcompetitie.seizoen = seizoen
            histcompetitie.comp_type = comp_type
            histcompetitie.klasse = klasse
            histcompetitie.is_team = False
            histcompetitie.save()

        return histcompetitie

    def _convert_scores(self, scores):
        count = 0
        totaal = 0
        getallen = list()
        for score in scores:
            getal = int(score)
            getallen.append(getal)
            if getal:
                count += 1
                totaal += getal
            # for
        return scores, count, totaal

    def _import(self, lines, seizoen, comptype):
        # sanity-check voor de hele file
        linenr = 0
        for line in lines:
            linenr += 1
            spl = line.split(';')
            if len(spl) != 11:
                self.stderr.write("[ERROR] Fout in regel %s: niet 11 kolommen" % linenr)
                self._count_error += 1

            if linenr > 1 and spl[2] not in TOEGESTANE_KLASSEN:
                self.stderr.write('[ERROR] Regel %s: onbekende klasse %s' % (linenr, repr(spl[1])))
                self._count_error += 1
        # for

        if lines[0].split(";")[0] != "bondsnummer":
            self.stderr.write("[ERROR] Eerste regels bevat geen headers: %s" % repr(lines[0]))
            self._count_error += 1
        del lines[0]

        if self._count_error > 0:
            return

        histcomps = dict()  # ['klasse'] = HistCompetitie()
        rank = dict()       # ['klasse'] = int

        bulk = list()
        line_nr = 0
        for line in lines:
            line_nr += 1
            spl = line.strip().split(";")
            #self.stdout.write(repr(spl))
            # spl = [nhb_nr, klasse, score1..7, gemiddelde]

            nhb_nr = spl[0]

            ver_nr = spl[1]

            klasse = spl[2]
            try:
                histcompetitie = histcomps[klasse]
            except KeyError:
                # nieuwe klasse
                histcomps[klasse] = histcompetitie = self.make_or_find_histcompetitie(seizoen, comptype, klasse)
                rank[klasse] = 1
            else:
                rank[klasse] += 1

            # fataseer een redelijk boogtype voor elke klasse
            # dit helpt in het bepalen van het aanvangsgemiddelde voor een competitieklasse
            if "Recurve" in klasse:
                boogtype = "R"
            elif "Compound" in klasse:
                boogtype = "C"
            elif "Barebow" in klasse:
                boogtype = "BB"
            elif "Longbow" in klasse:
                boogtype = "LB"
            elif "Instinctive" in klasse:
                boogtype = "IB"
            else:
                boogtype = "?"
                self.stdout.write('[WARNING] Onzeker welk boogtype voor klasse %s' % repr(klasse))
                self._count_skip += 1
                continue

            # overslaan als er niet ten minste 6 scores zijn
            scores, count, totaal = self._convert_scores(spl[3:3+7])
            if count < 6:
                # silently skip
                continue

            # lid erbij zoeken voor de schutter naam en vereniging
            try:
                lid = NhbLid.objects.get(nhb_nr=nhb_nr)
            except NhbLid.DoesNotExist:
                self.stdout.write("[WARNING] Lid %s wordt overgeslagen kan naam niet opzoeken (geen lid meer)" % nhb_nr)
                self._count_skip += 1
                continue

            try:
                ver = NhbVereniging.objects.get(nhb_nr=ver_nr)
                ver_naam = ver.naam
            except NhbVereniging.DoesNotExist:
                # fall-back voor recent verwijderde verenigingen
                if ver_nr == '1058':
                    ver_naam = 'Willem Tell'
                elif ver_nr == '1093':
                    ver_naam = 'De Bosjagers'
                elif ver_nr == '1147':
                    ver_naam = 'Diana'
                elif ver_nr == '1170':
                    ver_naam = 'Batavieren Treffers'
                else:
                    ver_naam = '?'
                    self.stdout.write('[WARNING] Kan geen naam opzoeken voor verwijderde vereniging %s' % ver_nr)

            gemiddelde = float(spl[10].replace(',', '.'))    # 9,123 --> 9.123

            hist = HistCompetitieIndividueel()
            hist.histcompetitie = histcompetitie
            hist.rank = rank[klasse]
            hist.schutter_nr = nhb_nr
            hist.schutter_naam = " ".join([lid.voornaam, lid.achternaam])
            hist.boogtype = boogtype
            hist.vereniging_nr = ver_nr
            hist.vereniging_naam = ver_naam
            hist.score1 = scores[0]
            hist.score2 = scores[1]
            hist.score3 = scores[2]
            hist.score4 = scores[3]
            hist.score5 = scores[4]
            hist.score6 = scores[5]
            hist.score7 = scores[6]
            hist.gemiddelde = gemiddelde
            hist.totaal = totaal

            # check if the record already exists
            dupe = HistCompetitieIndividueel.objects.filter(
                        histcompetitie=hist.histcompetitie,
                        schutter_nr=hist.schutter_nr,
                        vereniging_nr=hist.vereniging_nr)
            if len(dupe) > 0:
                self._count_dupe += 1
            else:
                bulk.append(hist)
                self._count_added += 1
                if len(bulk) >= 100:
                    HistCompetitieIndividueel.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk):
            HistCompetitieIndividueel.objects.bulk_create(bulk)

    def handle(self, *args, **options):
        # self.stderr.write("import individuele competitie historie. args=%s, options=%s" % (repr(args), repr(options)))
        self.verbose = options['verbose']

        seizoen = options['seizoen'][0]
        if len(seizoen) != 9 or seizoen[4] != "-":
            self.stderr.write("[ERROR] Seizoen moet een range zijn, bijvoorbeeld 2010-2011 (was %s)" % repr(jaar))
            return

        try:
            lines = options['filename'][0].readlines()
        except UnicodeDecodeError as exc:
            self.stderr.write("File has format issues (%s)" % str(exc))
            return

        self._count_dupe = 0
        self._count_added  =0
        self._count_error = 0
        self._count_skip = 0
        linecount = len(lines)

        self._import(lines, options['seizoen'][0], options['comptype'][0])

        self.stdout.write("Read %s lines; skipped %s dupes; %s skipped; %s skip with errors; added %s records" % (linecount, self._count_dupe, self._count_skip, self._count_error, self._count_added))

# end of file

