# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from django.utils import timezone
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
import os


class Command(BaseCommand):
    help = "Data van de oude site overnemen"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._afstand = 0
        self._comp = None
        self._klasse = None
        self._boogtype = None

        # datum/tijd stempel voor alle nieuwe ScoreHist
        self._import_when = timezone.now()

        # wordt opgezet door _prep_regio2deelcomp_regio2ronde2uitslag
        self._regio2deelcomp = None        # [regio_nr] = DeelCompetitie
        self._regio2ronde2uitslag = None   # [regio_nr] = [1..7] = WedstrijdUitslag

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

                beschrijving = "Ronde %s oude prg" % ronde    # max 20 chars!

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

    def add_arguments(self, parser):
        parser.add_argument('pad', nargs=1, help="Pad naar directory met opgehaalde rayonuitslagen (.html)")

    def selecteer_klasse(self, klasse):
        self._klasse = (CompetitieKlasse
                        .objects
                        .get(competitie=self._comp,
                             indiv__buiten_gebruik=False,
                             indiv__beschrijving__iexact=klasse))

    def vind_schutterboog(self, lid):
        # schutterboog record vinden / aanmaken
        # boogtype aanzetten voor wedstrijden
        # aanvangsgemiddelde record aanmaken
        schutterboog, _ = SchutterBoog.objects.get_or_create(nhblid=lid,
                                                             boogtype=self._boogtype)
        if not schutterboog.voor_wedstrijd:
            schutterboog.voor_wedstrijd = True
            schutterboog.save()

        return schutterboog

    def vind_of_maak_ag(self, schutterboog, ag):
        if ag:
            gemiddelde = Decimal(ag)
        else:
            gemiddelde = AG_NUL
        waarde = int(gemiddelde * 1000)

        try:
            score = (Score
                     .objects
                     .get(is_ag=True,
                          schutterboog=schutterboog,
                          afstand_meter=self._afstand))
        except Score.DoesNotExist:
            score = Score()
            score.is_ag = True
            score.schutterboog = schutterboog
            score.afstand_meter = self._afstand
            score.waarde = waarde
            if waarde > 0:
                # alleen opslaan als dit een zinnige AG is
                # anders geven we wel het record terug zodat de cod gelijk kan blijven
                score.save()
        else:
            if waarde != score.waarde:
                self.stdout.write(
                    '[WARNING] Verschil in AG voor nhbnr %s: bekend=%.3f, in uitslag=%.3f' % (
                        schutterboog.nhblid.nhb_nr, score.waarde / 1000, gemiddelde))

        return score

    def vind_of_maak_inschrijving(self, deelcomp, schutterboog, lid_vereniging, ag):
        # zoek de RegioCompetitieSchutterBoog erbij
        try:
            inschrijving = (RegioCompetitieSchutterBoog
                            .objects
                            .get(deelcompetitie=deelcomp,
                                 schutterboog=schutterboog))
        except RegioCompetitieSchutterBoog.DoesNotExist:
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
            inschrijving.save()

        return inschrijving

    def uitslag_opslaan(self, deelcomp, inschrijving, scores):
        regio_nr = deelcomp.nhb_regio.regio_nr

        # zoek naar alle scores van deze schutter
        score_pks = (Score
                     .objects
                     .filter(schutterboog=inschrijving.schutterboog,
                             is_ag=False,
                             afstand_meter=self._afstand)
                     .values_list('pk', flat=True))
        # print('score_pks: %s' % score_pks)

        for ronde in range(1, 7+1):
            notitie = "Importeer scores van uitslagen.handboogsport.nl voor ronde %s" % ronde

            waarde = scores[ronde - 1]
            if waarde:                  # filter leeg
                waarde = int(waarde)
                if waarde:              # filter 0
                    # zoek de uitslag van de virtuele wedstrijd erbij
                    uitslag = self._regio2ronde2uitslag[regio_nr][ronde]

                    # zoek het score-geschiedenis record erbij
                    #  voor de scores van deze schutter
                    #   in deze ronde
                    hists = (ScoreHist
                             .objects
                             .filter(notitie=notitie,
                                     score__pk__in=score_pks))

                    if len(hists) == 0:
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
                    else:
                        # structuur bestond al
                        # kijk of de score gewijzigd is
                        score = hists[0].score
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

    def parse_tabel_cells(self, cells):
        # cellen: rank, schutter, vereniging, AG, scores 1..7, VSG, totaal
        # print('cells: %s' % repr(cells))

        # schutter: [123456] Volledige Naam
        nhb_nr = cells[1][1:1+6]       # afkappen voor veiligheid
        naam = cells[1][9:]

        try:
            lid = (NhbLid
                   .objects
                   .select_related('bij_vereniging',
                                   'bij_vereniging__regio')
                   .get(nhb_nr=nhb_nr))
        except NhbLid.DoesNotExist:
            self.stdout.write('[WARNING] Kan lid %s niet vinden' % nhb_nr)
            return

        if naam != lid.volledige_naam():
            self.stdout.write('[WARNING] Verschil in lid %s naam: bekend=%s, oude programma=%s' % (lid.nhb_nr, lid.volledige_naam(), naam))

        if not lid.bij_vereniging:
            self.stderr.write('[ERROR] Lid %s heeft geen vereniging en wordt dus niet ingeschreven' % nhb_nr)
            return

        if str(lid.bij_vereniging) != cells[2]:
            # vind de oude vereniging, want die moeten we opslaan bij de inschrijving
            ver_nr = cells[2][1:1+4]       # afkappen voor veiligheid
            lid_ver = NhbVereniging.objects.get(nhb_nr=ver_nr)
            if str(lid_ver) != cells[2]:
                self.stdout.write('[WARNING] Verschil in vereniging naam: bekend=%s, oude programma=%s' % (str(lid_ver), cells[2]))
        else:
            lid_ver = lid.bij_vereniging

        deelcomp = self._regio2deelcomp[lid.bij_vereniging.regio.regio_nr]

        # zorg dat de schutter-boog records er zijn en de voorkeuren ingevuld zijn
        schutterboog = self.vind_schutterboog(lid)
        score_ag = self.vind_of_maak_ag(schutterboog, cells[3])

        klasse_min_ag = int(self._klasse.min_ag * 1000)
        if score_ag.waarde < klasse_min_ag:
            self.stdout.write(
                '[WARNING] schutter %s heeft te laag AG (%.3f) voor klasse %s' % (
                      nhb_nr, score_ag.waarde / 1000, self._klasse))

        inschrijving = self.vind_of_maak_inschrijving(deelcomp, schutterboog, lid_ver, cells[3])

        self.uitslag_opslaan(deelcomp, inschrijving, cells[4:4+7])

    def parse_tabel_regel(self, html):
        if html.find('<td class="blauw">') >= 0:
            # overslaan: header regel boven aan de lijst
            return

        if html.find('<td colspan=15>&nbsp;</td>') > 0:
            # overslaan: lege regel voor de nieuwe wedstrijdklasse
            return

        pos = html.find('<td colspan=15><b>')
        if pos > 0:
            # nieuwe klasse
            html = html[pos+18:]
            pos = html.find('</b>')
            if pos < 0:
                self.stderr.write('[ERROR] Kan einde wedstrijdklasse niet vinden: %s' % repr(html))
            else:
                self.selecteer_klasse(html[:pos])
            return

        # 'gewone' regel met een deelnemer, AG, scores, VSG en totaal
        cells = list()
        while len(html) > 0:
            pos = html.find('<td')
            if pos >= 0:
                html = html[pos+3:]
                pos = html.find('>')
                html = html[pos+1:]

                pos = html.find('</td>')
                cell = html[:pos]

                cell = cell.replace('&nbsp;&nbsp;&nbsp;', ' ')
                cell = cell.replace('<font color="#FF0000">', '')
                cell = cell.replace('</font>', '')

                if cell == '&nbsp;':
                    cell = ''

                cells.append(cell)

                html = html[pos+5:]
            else:
                html = ''
        # while
        self.parse_tabel_cells(cells)

    def parse_html_table(self, html):
        if html.find('class="blauw">') < 0:
            # ignore want niet de tabel met de scores
            return

        while len(html) > 0:
            pos = html.find('<tr')
            if pos < 0:
                # geen nieuwe regel meer kunnen vinden
                html = ''
            else:
                html = html[pos:]
                pos = html.find('</tr>')
                if pos < 0:
                    self.stderr.write('[ERROR] Kan einde regel onverwacht niet vinden')
                    html = ''
                else:
                    self.parse_tabel_regel(html[:pos])
                    html = html[pos+5:]
        # while

    def parse_html(self, html):
        # html pagina bestaat uit tabellen met regels en cellen
        while len(html) > 0:
            pos = html.find('<table ')
            if pos < 0:
                # geen table meer --> klaar
                html = ''
            else:
                html = html[pos:]
                pos = html.find('</table>')
                if pos < 0:
                    self.stderr.write('[ERROR] Kan einde tabel onverwacht niet vinden')
                    html = ''
                else:
                    self.parse_html_table(html[:pos])
                    html = html[pos+8:]
        # while

    def read_html(self, fname):
        self.stdout.write("[INFO] Inlezen: " + repr(fname))
        try:
            html = open(fname, "r").read()
        except FileNotFoundError:
            self.stderr.write('[ERROR] Failed to open %s' % fname)
        else:
            self.parse_html(html)

    def handle(self, *args, **options):
        pad = options['pad'][0]

        for afstand in (18, 25):
            self._afstand = afstand
            fname1 = str(afstand)
            self._comp = Competitie.objects.get(afstand=afstand)
            self._prep_regio2deelcomp_regio2ronde2uitslag()

            for afkorting in ('R', 'C', 'BB', 'IB', 'LB'):
                self._boogtype = BoogType.objects.get(afkorting=afkorting)
                fname2 = fname1 + '_' + afkorting + '_rayon'

                for rayon in ('1', '2', '3', '4'):
                    fname3 = fname2 + rayon + ".html"
                    self.read_html(os.path.join(pad, fname3))
            # for
        # for

        activiteit = "Competitie inschrijvingen en scores aangevuld vanuit het oude programma"

        # schrijf in het logboek
        schrijf_in_logboek(account=None,
                           gebruikte_functie='oude_site_overnemen (command line)',
                           activiteit=activiteit)
        self.stdout.write(activiteit)

# end of file
