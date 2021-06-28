# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

import argparse
from django.core.management.base import BaseCommand
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from NhbStructuur.models import NhbLid, NhbVereniging


TOEGESTANE_KLASSEN = ('Recurve', 'Compound', 'Barebow', 'Longbow', 'Instinctive Bow')


class Command(BaseCommand):
    help = "Importeer historische competitie uitslag, individueel"
    verbose = False

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self._count_not6scores = 0
        self._count_noname = 0
        self._count_skip = 0
        self._count_error = 0
        self._count_added = 0
        self._count_dupe = 0
        self._count_dupe_bow = 0
        self._boogtype2histcomp = dict()     # [boogtype] = HistCompetitie

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=argparse.FileType("r"),
                            help="in te lezen file")
        parser.add_argument('seizoen', nargs=1,
                            help="competitie seizoen: 20xx/20yy")
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

    def _verwijder_eerdere_import(self, seizoen, comptype):
        objs = HistCompetitie.objects.filter(seizoen=seizoen, comp_type=comptype)
        if len(objs):
            objs.delete()

    @staticmethod
    def _convert_scores(scores):
        aantal = 0
        totaal = 0
        getallen = list()
        for score in scores:
            getal = int(score)
            getallen.append(getal)
            if getal:
                aantal += 1
                totaal += getal
            # for
        return getallen, aantal, totaal

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

        histcomps = dict()      # ['klasse'] = HistCompetitie()
        indiv_scores = list()   # (gem, scores, HistCompetitieIndividueel)

        bulk = list()
        line_nr = 0
        for line in lines:
            line_nr += 1
            spl = line.strip().split(";")
            # spl = [nhb_nr, klasse, score1..7, gemiddelde]

            nhb_nr = spl[0]

            ver_nr = spl[1]

            klasse = spl[2]     # boogtype
            try:
                histcompetitie = histcomps[klasse]
            except KeyError:
                # nieuwe klasse
                histcomps[klasse] = histcompetitie = self.make_or_find_histcompetitie(seizoen, comptype, klasse)

            # fantaseer een redelijk boogtype voor elke klasse
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
                self.stdout.write('[WARNING] Onzeker welk boogtype voor klasse %s' % repr(klasse))
                self._count_skip += 1
                continue

            self._boogtype2histcomp[boogtype] = histcompetitie

            # overslaan als er niet ten minste 6 scores zijn
            scores, _, totaal = self._convert_scores(spl[3:3+7])

            # naam van het lid erbij zoeken (spelling in CRM is leidend)
            try:
                lid = NhbLid.objects.get(nhb_nr=nhb_nr)
            except NhbLid.DoesNotExist:
                # kan naam nu niet vonden - toch importeren en later aanvullen
                print("[WARNING] Kan naam niet vinden bij nhb nummer %s" % repr(nhb_nr))
                lid = None
                self._count_noname += 1

            # naam van de vereniging opzoeken en opslaan
            try:
                ver = NhbVereniging.objects.get(ver_nr=ver_nr)
                ver_naam = ver.naam
            except NhbVereniging.DoesNotExist:
                # fall-back voor recent verwijderde verenigingen
                if ver_nr == '1026':
                    ver_naam = 'Victoria'
                elif ver_nr == '1058':
                    ver_naam = 'Willem Tell'
                elif ver_nr == '1093':
                    ver_naam = 'De Bosjagers'
                elif ver_nr == '1147':
                    ver_naam = 'Diana'
                elif ver_nr == '1152':
                    ver_naam = 'Ons Genoegen'
                elif ver_nr == '1170':
                    ver_naam = 'Batavieren Treffers'
                elif ver_nr == '1191':
                    ver_naam = 'Eendracht St Sebast'
                elif ver_nr == '1226':
                    ver_naam = 'Centaur Asten'
                else:
                    ver_naam = '?'
                    self.stdout.write('[WARNING] Kan geen naam opzoeken voor verwijderde vereniging %s' % ver_nr)

            gemiddelde = float(spl[10].replace(',', '.'))    # 9,123 --> 9.123

            hist = HistCompetitieIndividueel()
            hist.histcompetitie = histcompetitie
            hist.rank = 0
            hist.schutter_nr = nhb_nr
            if lid:
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

            scores.sort(reverse=True)
            lowest = scores[-1]
            if hist.score7 == lowest:
                hist.laagste_score_nr = 7
            elif hist.score6 == lowest:
                hist.laagste_score_nr = 6
            elif hist.score5 == lowest:
                hist.laagste_score_nr = 5
            elif hist.score4 == lowest:
                hist.laagste_score_nr = 4
            elif hist.score3 == lowest:
                hist.laagste_score_nr = 3
            elif hist.score2 == lowest:
                hist.laagste_score_nr = 2
            else:
                hist.laagste_score_nr = 1

            hist.gemiddelde = gemiddelde
            hist.totaal = totaal - lowest

            # check if the record already exists
            dupe = HistCompetitieIndividueel.objects.filter(
                        histcompetitie=hist.histcompetitie,
                        schutter_nr=hist.schutter_nr,
                        vereniging_nr=hist.vereniging_nr)
            if len(dupe) > 0:
                tup = (gemiddelde, scores, len(indiv_scores), dupe[0])
                indiv_scores.append(tup)
                self._count_dupe += 1
            else:
                tup = (gemiddelde, scores, len(indiv_scores), hist)
                indiv_scores.append(tup)
                bulk.append(hist)
                self._count_added += 1
                if len(bulk) >= 100:
                    HistCompetitieIndividueel.objects.bulk_create(bulk)
                    bulk = list()

        # for

        if len(bulk):
            HistCompetitieIndividueel.objects.bulk_create(bulk)

        # deel de rank nummers opnieuw uit
        ranks = dict()       # ['boogtype'] = int

        indiv_scores.sort(reverse=True)
        for gem, scores, nr, hist in indiv_scores:
            try:
                ranks[hist.boogtype] += 1
                hist.rank = ranks[hist.boogtype]
            except KeyError:
                hist.rank = 1
                ranks[hist.boogtype] = hist.rank

            hist.save()
        # for

    def _delete_dupes(self):
        """ Sommige BB/IB/LB schutters staan in de geïmporteerde data OOK genoemd
                in de recurve klasse, met exact dezelfde scores.
            Dit was nodig in het oude programma voor het team schieten waarbij een
                Recurve team ook BB/IB/LB schutters mag bevatten.
            Andere schutters schieten zowel de R als C klasse of the BB en R klasse
                en hebben dan niet dezelfde scores.

            Zoek de NHB nummers van R schutters die ook in de BB/IB/LB voorkomen
            Als de scores ook overeen komen, verwijder dan het records in de R klasse.
        """
        self.stdout.write("[INFO] Removing duplicates from Recurve results (dupe with BB/IB/LB)")

        try:
            histcomp_r = self._boogtype2histcomp['R']
        except KeyError:
            return

        # doorloop de kleinste klassen
        for boogtype in ('BB', 'IB', 'LB'):
            for houtobj in HistCompetitieIndividueel.objects.filter(boogtype=boogtype,
                                                                    histcompetitie=self._boogtype2histcomp[boogtype]):
                # zoek dit nummer op in de Recurve klasse
                try:
                    robj = HistCompetitieIndividueel.objects.get(boogtype='R',
                                                                 histcompetitie=histcomp_r,
                                                                 schutter_nr=houtobj.schutter_nr)
                except HistCompetitieIndividueel.DoesNotExist:
                    pass
                else:
                    if houtobj.totaal == robj.totaal:
                        # controleer dat alle scores overeen komen
                        if (houtobj.score1 == robj.score1 and houtobj.score2 == robj.score2 and
                                houtobj.score3 == robj.score3 and houtobj.score4 == robj.score4 and
                                houtobj.score5 == robj.score5 and houtobj.score6 == robj.score6 and
                                houtobj.score7 == robj.score7):
                            # gevonden
                            # verwijder het recurve object
                            # hierdoor valt helaas een gat in de ranking
                            self._count_dupe_bow += 1
                            robj.delete()
                            # print("nhb_nr:%s, hout:%s, totaal_1:%s, totaal_2:%s" % (houtobj.schutter_nr, houtobj.boogtype, houtobj.totaal, robj.totaal))
                        # if
            # for
        # for

    def handle(self, *args, **options):
        # self.stderr.write("import individuele competitie historie. args=%s, options=%s" % (repr(args), repr(options)))
        self.verbose = options['verbose']

        comptype = options['comptype'][0]
        seizoen = options['seizoen'][0]
        if len(seizoen) != 9 or seizoen[4] != "/":
            self.stderr.write("[ERROR] Seizoen moet het formaat 'jaar/jaar+1' hebben, bijvoorbeeld '2010/2011' (was %s)" % repr(seizoen))
            return

        try:
            lines = options['filename'][0].readlines()
        except UnicodeDecodeError as exc:
            self.stderr.write("File has format issues (%s)" % str(exc))
            return

        linecount = len(lines)

        # verwijder de eerder geïmporteerde uitslag
        self._verwijder_eerdere_import(seizoen, comptype)
        self._import(lines, seizoen, comptype)
        self._delete_dupes()

        self.stdout.write("Read %s lines; skipped %s dupes; %s skipped;"
                          " %s skip with errors; %s skip dupe bow score; added %s records;"
                          " %s without name" % (linecount, self._count_dupe, self._count_skip,
                                                self._count_error, self._count_dupe_bow,
                                                self._count_added - self._count_dupe_bow,
                                                self._count_noname))

# end of file
