# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid, NhbVereniging
from Logboek.models import schrijf_in_logboek
from Competitie.models import (Competitie, CompetitieKlasse,
                               LAAG_REGIO, DeelCompetitie, DeelcompetitieRonde,
                               AG_NUL, RegioCompetitieSchutterBoog)
from Schutter.models import SchutterBoog
from Wedstrijden.models import Wedstrijd, WedstrijdUitslag, WedstrijdenPlan
from Score.models import Score, ScoreHist
from decimal import Decimal
import datetime
import hashlib
import sys
import os


class Command(BaseCommand):
    help = "Data van de oude site overnemen"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._afstand = 0
        self._comp = None
        self._klasse = None
        self._boogtype = None
        self._dryrun = False
        self._count_errors = 0
        self._count_warnings = 0
        self._warnings = list()            # al geroepen warnings

        # datum/tijd stempel voor alle nieuwe ScoreHist
        self._import_when = None

        # wordt opgezet door _prep_regio2deelcomp_regio2ronde2uitslag
        self._regio2deelcomp = None        # [regio_nr] = DeelCompetitie
        self._regio2ronde2uitslag = None   # [regio_nr] = [1..7] = WedstrijdUitslag

        self._ingelezen = list()           # tuple(afstand, nhbnr, boogtype, score1, ..., score 7)
        self._verwijder_r_18 = list()
        self._verwijder_r_25 = list()
        self._verwijder = None             # wijst naar _verwijder_r_18 of _verwijder_r_25, afhankelijk van afstand

        self._cache_klasse = dict()        # [competitie.pk, klasse_beschrijving] = CompetitieKlasse
        self._cache_nhblid = dict()        # [nhbnr] = NhbLid
        self._cache_schutterboog = dict()  # [(nhblid, afkorting)] = SchutterBoog
        self._cache_inschrijving = dict()  # [(deelcomp.pk, schutterboog.pk)] = RegioCompetitieSchutterBoog
        self._cache_ag_score = dict()      # [(afstand, schutterboog.pk)] = Score
        self._cache_scores = dict()        # [(inschrijving.pk, ronde.pk)] = score

        self._prev_hash = dict()           # [fname] = hash

    def _roep_warning(self, msg):
        # print en tel waarschuwingen
        # en onderdruk dubbele berichten
        if msg not in self._warnings:
            self._warnings.append(msg)
            self._count_warnings += 1
            self.stdout.write(msg)

    def _prep_caches(self):
        # bouw caches om herhaaldelijke database toegang te voorkomen, voor performance
        for obj in (CompetitieKlasse
                    .objects
                    .select_related('competitie', 'indiv')
                    .exclude(indiv__buiten_gebruik=True)):
            tup = (obj.competitie.pk, obj.indiv.beschrijving.lower())
            self._cache_klasse[tup] = obj
        # for

        for obj in (NhbLid
                    .objects
                    .select_related('bij_vereniging',
                                    'bij_vereniging__regio')
                    .all()):
            self._cache_nhblid[str(obj.nhb_nr)] = obj
        # for

        for obj in (SchutterBoog
                    .objects
                    .select_related('nhblid', 'boogtype')
                    .all()):
            tup = (obj.nhblid.nhb_nr, obj.boogtype.afkorting)
            self._cache_schutterboog[tup] = obj
        # for

        afstand_schutterboog_pk2inschrijving = dict()
        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .select_related('deelcompetitie',
                                    'deelcompetitie__competitie',
                                    'schutterboog',
                                    'bij_vereniging')
                    .all()):
            tup = (obj.deelcompetitie.pk, obj.schutterboog.pk)
            self._cache_inschrijving[tup] = obj

            tup = (obj.deelcompetitie.competitie.afstand, obj.schutterboog.pk)
            afstand_schutterboog_pk2inschrijving[tup] = obj
        # for

        for obj in (Score
                    .objects
                    .select_related('schutterboog')
                    .filter(is_ag=True,
                            afstand_meter__in=(18, 25))
                    .all()):
            tup = (obj.afstand_meter, obj.schutterboog.pk)
            self._cache_ag_score[tup] = obj
        # for

        for hist in(ScoreHist
                    .objects
                    .select_related('score', 'score__schutterboog')
                    .filter(score__is_ag=False,
                            notitie__startswith="Importeer scores van uitslagen.handboogsport.nl voor ronde ")):
            ronde = int(hist.notitie[-1])
            score = hist.score
            tup = (str(score.afstand_meter), score.schutterboog.pk)
            try:
                inschrijving = afstand_schutterboog_pk2inschrijving[tup]
            except KeyError:
                pass
            else:
                tup = (inschrijving.pk, ronde)
                self._cache_scores[tup] = score
        # for

    def _prep_regio2deelcomp_regio2ronde2uitslag(self):
        # maak vertaling van vereniging naar deelcompetitie
        # wordt aangeroepen voor elke competitie (18/25)

        self._regio2deelcomp = dict()
        self._regio2ronde2uitslag = dict()

        nul_uur = datetime.time(hour=0, minute=0, second=0)

        if self._afstand == 18:
            max_score = 300
        else:
            max_score = 250

        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('nhb_regio')
                         .filter(laag=LAAG_REGIO,
                                 competitie=self._comp)
                         .all()):

            regio_nr = deelcomp.nhb_regio.regio_nr

            self._regio2deelcomp[regio_nr] = deelcomp

            # zorg dat het plan wedstrijden heeft voor geïmporteerde regiocompetitie scores
            # 1 wedstrijd voor elke ronde
            self._regio2ronde2uitslag[regio_nr] = dict()

            for ronde in range(1, 7+1):
                self._regio2ronde2uitslag[regio_nr][ronde] = dict()

                beschrijving = "Ronde %s oude programma" % ronde

                try:
                    deelcomp_ronde = (DeelcompetitieRonde
                                      .objects
                                      .get(beschrijving=beschrijving,
                                           deelcompetitie=deelcomp))
                except DeelcompetitieRonde.DoesNotExist:
                    # geen ronde met een plan met die naam
                    # maak een nieuwe aan

                    plan = WedstrijdenPlan()
                    plan.bevat_hiaat = False
                    plan.save()

                    deelcomp_ronde = DeelcompetitieRonde()
                    deelcomp_ronde.deelcompetitie = deelcomp
                    deelcomp_ronde.week_nr = 37
                    deelcomp_ronde.beschrijving = beschrijving
                    deelcomp_ronde.plan = plan
                    deelcomp_ronde.save()

                beschrijving = "Resultaat van uitslagen.handboogsport.nl regio %s ronde %s" % (regio_nr, ronde)

                try:
                    wedstrijd = deelcomp_ronde.plan.wedstrijden.get(beschrijving=beschrijving)
                except Wedstrijd.DoesNotExist:
                    # maak een nieuwe wedstrijd aan
                    wedstrijd = Wedstrijd()
                    wedstrijd.beschrijving = beschrijving
                    wedstrijd.preliminair = False
                    wedstrijd.datum_wanneer = datetime.date.today()
                    wedstrijd.tijd_begin_aanmelden = nul_uur
                    wedstrijd.tijd_begin_wedstrijd = nul_uur
                    wedstrijd.tijd_einde_wedstrijd = nul_uur
                    wedstrijd.save()

                    deelcomp_ronde.plan.wedstrijden.add(wedstrijd)

                # zorg dat de wedstrijd een uitslag heeft
                if not wedstrijd.uitslag:
                    uitslag = WedstrijdUitslag()
                    uitslag.max_score = max_score
                    uitslag.afstand_meter = self._afstand
                    uitslag.save()

                    wedstrijd.uitslag = uitslag
                    wedstrijd.save()

                self._regio2ronde2uitslag[regio_nr][ronde] = wedstrijd.uitslag
            # for
        # for

    def _calc_hash(self, msg):
        return hashlib.md5(msg.encode('UTF-8')).hexdigest()

    def _selecteer_klasse(self, beschrijving):
        tup = (self._comp.pk, beschrijving.lower())
        try:
            self._klasse = self._cache_klasse[tup]
        except KeyError:
            self.stderr.write('[ERROR] Kan wedstrijdklasse %s niet vinden (competitie %s)' % (repr(beschrijving), self._comp))
            self._count_errors += 1

    def _vind_schutterboog(self, lid):
        # schutterboog record vinden / aanmaken
        # boogtype aanzetten voor wedstrijden
        # aanvangsgemiddelde record aanmaken

        tup = (lid.nhb_nr, self._boogtype.afkorting)

        try:
            schutterboog = self._cache_schutterboog[tup]
        except KeyError:
            schutterboog, _ = SchutterBoog.objects.get_or_create(nhblid=lid,
                                                                 boogtype=self._boogtype)
            self._cache_schutterboog[tup] = schutterboog

        if not schutterboog.voor_wedstrijd:
            schutterboog.voor_wedstrijd = True
            schutterboog.save()

        return schutterboog

    def _vind_of_maak_ag(self, schutterboog, ag):
        if ag:
            gemiddelde = Decimal(ag)
        else:
            gemiddelde = AG_NUL
        waarde = int(gemiddelde * 1000)

        tup = (self._afstand, schutterboog.pk)
        try:
            score = self._cache_ag_score[tup]
        except KeyError:
            score = Score()
            score.is_ag = True
            score.schutterboog = schutterboog
            score.afstand_meter = self._afstand
            score.waarde = waarde
            if waarde > 0:
                # alleen opslaan als dit een zinnige AG is
                # anders geven we wel het record terug zodat de code gelijk kan blijven
                if not self._dryrun:
                    score.save()
            self._cache_ag_score[tup] = score

        return score, waarde

    def _vind_of_maak_inschrijving(self, deelcomp, schutterboog, lid_vereniging, ag):
        # zoek de RegioCompetitieSchutterBoog erbij
        tup = (deelcomp.pk, schutterboog.pk)
        try:
            inschrijving = self._cache_inschrijving[tup]
        except KeyError:
            # schrijf de schutter in
            inschrijving = RegioCompetitieSchutterBoog()
            inschrijving.deelcompetitie = deelcomp
            inschrijving.schutterboog = schutterboog
            inschrijving.bij_vereniging = lid_vereniging
            inschrijving.klasse = self._klasse

            if ag:
                inschrijving.aanvangsgemiddelde = ag
            else:
                inschrijving.aanvangsgemiddelde = AG_NUL
            if not self._dryrun:
                inschrijving.save()

            self._cache_inschrijving[tup] = inschrijving

        return inschrijving

    def _uitslag_opslaan(self, deelcomp, inschrijving, scores):
        aantal_scores = 0
        regio_nr = deelcomp.nhb_regio.regio_nr

        for ronde in range(1, 7+1):
            notitie = "Importeer scores van uitslagen.handboogsport.nl voor ronde %s" % ronde

            waarde = scores[ronde - 1]
            if waarde:                  # filter leeg
                waarde = int(waarde)
                if waarde:              # filter 0
                    # zoek de uitslag van de virtuele wedstrijd erbij
                    uitslag = self._regio2ronde2uitslag[regio_nr][ronde]
                    aantal_scores += 1

                    tup = (inschrijving.pk, ronde)
                    try:
                        score = self._cache_scores[tup]
                    except KeyError:
                        # eerste keer: maak het record + score aan
                        score = Score()
                        score.is_ag = False
                        score.afstand_meter = self._afstand
                        score.schutterboog = inschrijving.schutterboog
                        score.waarde = waarde
                        score.save()

                        hist = ScoreHist()
                        hist.score = score
                        hist.oude_waarde = 0
                        hist.nieuwe_waarde = waarde
                        hist.when = self._import_when
                        hist.notitie = notitie
                        hist.save()

                        uitslag.scores.add(score)

                        self._cache_scores[tup] = score
                    else:
                        # kijk of de score gewijzigd is
                        if score.waarde != waarde:
                            # sla de aangepaste score op
                            hist = ScoreHist()
                            hist.score = score
                            hist.oude_waarde = score.waarde
                            hist.nieuwe_waarde = waarde
                            hist.when = self._import_when
                            hist.notitie = notitie
                            hist.save()

                            score.waarde = waarde
                            score.save()
        # for

        return aantal_scores

    def _parse_tabel_cells(self, cells):
        # cellen: rank, schutter, vereniging, AG, scores 1..7, VSG, totaal
        # self.stdout.write('[DEBUG] cells: %s' % repr(cells))

        # schutter: [123456] Volledige Naam
        nhb_nr = cells[1][1:1+6]       # afkappen voor veiligheid
        naam = cells[1][9:]

        if self._boogtype.afkorting in ('BB', 'IB', 'LB'):
            tup = tuple([self._afstand, nhb_nr, self._boogtype.afkorting] + cells[4:4+7])
            self._ingelezen.append(tup)
        elif self._boogtype.afkorting == 'R':
            # kijk of dit een dupe is met een houtboog uitslag
            # dit ivm het dupliceren van uitslagen onder Recurve voor de teamcompetitie
            for afkorting in ('BB', 'IB', 'LB'):
                tup = tuple([self._afstand, nhb_nr, afkorting] + cells[4:4+7])
                if tup in self._ingelezen:
                    self._roep_warning('[WARNING] Sla dubbele invoer onder recurve (%sm) over: %s (scores: %s)' % (self._afstand, nhb_nr, ",".join(cells[4:4+7])))
                    self._verwijder.append(nhb_nr)
                    return

        try:
            lid = self._cache_nhblid[nhb_nr]
        except KeyError:
            self._roep_warning('[WARNING] Kan lid %s niet vinden' % nhb_nr)
            return

        if naam != lid.volledige_naam():
            self._roep_warning('[WARNING] Verschil in lid %s naam: bekend=%s, oude programma=%s' % (lid.nhb_nr, lid.volledige_naam(), naam))

        if not lid.bij_vereniging:
            # onderdruk deze melding zolang er geen scores zijn
            aantal_scores = len([1 for score in cells[4:4+7] if score and int(score) > 0])
            if aantal_scores > 0:
                self._roep_warning('[WARNING] Lid %s heeft %s scores maar geen vereniging en wordt dus niet ingeschreven' % (aantal_scores, nhb_nr))
            return

        if str(lid.bij_vereniging) != cells[2]:
            # vind de oude vereniging, want die moeten we opslaan bij de inschrijving
            ver_nr = cells[2][1:1+4]       # afkappen voor veiligheid
            try:
                lid_ver = NhbVereniging.objects.get(nhb_nr=ver_nr)
            except NhbVereniging.DoesNotExist:
                self.stderr.write('[ERROR] Vereniging %s is niet bekend' % ver_nr)
                self._count_errors += 1
                return
            else:
                if str(lid_ver) != cells[2]:
                    self._roep_warning('[WARNING] Verschil in vereniging naam: bekend=%s, oude programma=%s' % (str(lid_ver), cells[2]))
        else:
            lid_ver = lid.bij_vereniging

        deelcomp = self._regio2deelcomp[lid.bij_vereniging.regio.regio_nr]

        # zorg dat de schutter-boog records er zijn en de voorkeuren ingevuld zijn
        schutterboog = self._vind_schutterboog(lid)
        score_ag, waarde_ag = self._vind_of_maak_ag(schutterboog, cells[3])

        inschrijving = self._vind_of_maak_inschrijving(deelcomp, schutterboog, lid_ver, cells[3])

        if not self._dryrun:
            aantal_scores = self._uitslag_opslaan(deelcomp, inschrijving, cells[4:4 + 7])

            if aantal_scores > 1:
                if waarde_ag != score_ag.waarde:
                    self._roep_warning(
                        '[WARNING] Verschil in AG voor nhbnr %s: bekend=%.3f, in uitslag=%.3f' % (
                            schutterboog.nhblid.nhb_nr, score_ag.waarde / 1000, waarde_ag / 1000))

            # bij 3 scores wordt de schutter verplaatst van klasse onbekend naar andere klasse
            if aantal_scores < 3:
                klasse_min_ag = int(self._klasse.min_ag * 1000)
                if score_ag.waarde < klasse_min_ag:
                    self._roep_warning(
                        '[WARNING] schutter %s heeft te laag AG (%.3f) voor klasse %s' % (
                              nhb_nr, score_ag.waarde / 1000, self._klasse))

    def _parse_tabel_regel(self, html, pos2, pos_end):
        if html.find('<td class="blauw">', pos2, pos_end) >= 0:
            # overslaan: header regel boven aan de lijst
            return

        if html.find('<td colspan=15>&nbsp;</td>', pos2, pos_end) > 0:
            # overslaan: lege regel voor de nieuwe wedstrijdklasse
            return

        pos = html.find('<td colspan=15><b>', pos2, pos_end)
        if pos > 0:
            # nieuwe klasse
            html = html[pos+18:]
            pos = html.find('</b>')
            if pos < 0:
                self.stderr.write('[ERROR] Kan einde wedstrijdklasse niet vinden: %s' % repr(html))
                self._count_errors += 1
            else:
                self._selecteer_klasse(html[:pos])
            return

        # 'gewone' regel met een deelnemer, AG, scores, VSG en totaal
        cells = list()
        while pos2 < len(html):
            pos1 = html.find('<td', pos2, pos_end)
            if pos1 >= 0:
                # found the start of the next data cell
                # can be <td something=more>, or just <td>
                pos2 = html.find('>', pos1+3, pos_end)
                pos1 = pos2+1

                pos2 = html.find('</td>', pos1, pos_end)
                cell = html[pos1:pos2]
                pos2 += 5

                cell = cell.replace('&nbsp;&nbsp;&nbsp;', ' ')

                if cell == '&nbsp;':
                    cell = ''

                cells.append(cell)
            else:
                break   # from the while
        # while
        self._parse_tabel_cells(cells)

    def _parse_html_table(self, html, pos2, pos_end):
        if html.find('class="blauw">', pos2, pos_end) < 0:
            # ignore want niet de tabel met de scores
            return

        while pos2 < pos_end:
            pos1 = html.find('<tr', pos2, pos_end)
            if pos1 < 0:
                # geen nieuwe regel meer kunnen vinden
                pos2 = pos_end
            else:
                pos2 = html.find('</tr>', pos1, pos_end)
                if pos2 < 0:
                    self.stderr.write('[ERROR] Kan einde regel onverwacht niet vinden')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_tabel_regel(html, pos1, pos2)
                    pos2 += 5
        # while

    def _parse_html(self, html):
        # clean up unnecessary formatting
        html = html.replace('<font color="#FF0000">', '')
        html = html.replace('</font>', '')

        # html pagina bestaat uit tabellen met regels en cellen
        pos2 = 0
        while pos2 < len(html):
            pos1 = html.find('<table ', pos2)
            if pos1 < 0:
                # geen table meer --> klaar
                pos2 = len(html)
            else:
                pos2 = html.find('</table>', pos1)
                if pos2 < 0:
                    self.stderr.write('[ERROR] Kan einde tabel onverwacht niet vinden')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_html_table(html, pos1, pos2)
        # while

    def _read_html(self, fpath):
        try:
            html = open(fpath, "r").read()
        except FileNotFoundError:
            self.stderr.write('[ERROR] Failed to open %s' % fpath)
            self._count_errors += 1
        else:
            new_hash = self._calc_hash(html)
            fname = fpath.split('/')[-1]
            try:
                prev_hash = self._prev_hash[fname]
            except KeyError:
                pass
            else:
                if new_hash == prev_hash:
                    # self.stdout.write('[DEBUG] dupe')
                    return              # avoid duplicate processing

            self.stdout.write("[INFO] Verwerk " + repr(fpath))
            self._prev_hash[fname] = new_hash
            self._parse_html(html)

    def _lees_html_in_pad(self, pad):
        # filename: YYYYMMDD_HHMMSS_uitslagen
        spl = pad.split('/')
        grabbed_at = spl[-1][:15]
        self._import_when = datetime.datetime.strptime(grabbed_at, '%Y%m%d_%H%M%S')

        for afstand in (18, 25):
            self._afstand = afstand
            fname1 = str(afstand)
            self._comp = Competitie.objects.get(afstand=afstand)
            self._prep_regio2deelcomp_regio2ronde2uitslag()

            if afstand == 18:
                self._verwijder = self._verwijder_r_18
            else:
                self._verwijder = self._verwijder_r_25

            # doe R als laatste ivm verwijderen dubbelen door administratie teamcompetitie
            # (BB/IB/LB wordt met zelfde score onder Recurve gezet)
            for afkorting in ('C', 'BB', 'IB', 'LB', 'R'):
                self._boogtype = BoogType.objects.get(afkorting=afkorting)
                fname2 = fname1 + '_' + afkorting + '_rayon'

                for rayon in ('1', '2', '3', '4'):
                    fname3 = fname2 + rayon + ".html"
                    self._read_html(os.path.join(pad, fname3))
            # for
        # for

    def _verwijder_dubbele_deelnemers(self):
        # ruim op: eerder aangemaakte dubbele inschrijvingen (BB + R)
        #          dit kan gebeuren als een uitslag wel in de BB/IB/LB staat maar nog niet in R
        for afstand, nhb_nrs in (('18', self._verwijder_r_18),
                                 ('25', self._verwijder_r_25)):
            # zoek alle inschrijvingen die hier bij passen
            objs = (RegioCompetitieSchutterBoog
                    .objects
                    .filter(deelcompetitie__competitie__afstand=afstand,
                            schutterboog__nhblid__nhb_nr__in=nhb_nrs,
                            schutterboog__boogtype__afkorting='R')
                    .all())

            if objs.count() > 0:
                self._roep_warning('[WARNING] Verwijder %s dubbele inschrijvingen (%sm)' % (objs.count(), afstand))
                objs.delete()
        # for

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs=1, help="Pad naar directory met opgehaalde rayonuitslagen")
        parser.add_argument('max_fouten', nargs=1, type=int, help="Zet exit code bij meer dan dit aantal fouten")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        pad = os.path.normpath(options['dir'][0])
        max_fouten = options['max_fouten'][0]
        self._dryrun = options['dryrun']

        self._prep_caches()

        if options['all']:
            # pad wijst naar een top-dir
            # doorloop alle sub-directories
            subdirs = os.listdir(pad)       # geen volgorde garantie
            subdirs.sort()                  # wij willen oudste eerst
            for nr, subdir in enumerate(subdirs):
                print("Voortgang: %s van de %s" % (nr, len(subdirs)))
                self._lees_html_in_pad(os.path.join(pad, subdir))
            # for
        else:
            self._lees_html_in_pad(pad)

        self._verwijder_dubbele_deelnemers()

        activiteit = "Competitie inschrijvingen en scores aangevuld vanuit het oude programma"

        if self._dryrun:
            activiteit = "(DRY RUN) " + activiteit
        activiteit += " (waarschuwingen: %s, fouten: %s)" % (self._count_warnings, self._count_errors)

        # schrijf in het logboek
        if not self._dryrun:
            schrijf_in_logboek(account=None,
                               gebruikte_functie='oude_site_overnemen (command line)',
                               activiteit=activiteit)
        self.stdout.write(activiteit)

        if self._count_errors > max_fouten:
            sys.exit(1)


"""
    performance debug helper:
         
    from django.db import connection

        q_begin = len(connection.queries)

        # queries here

        print('queries: %s' % (len(connection.queries) - q_begin))
        for obj in connection.queries[q_begin:]:
            print('%10s %s' % (obj['time'], obj['sql'][:200]))
        # for
        sys.exit(1)
"""

# end of file
