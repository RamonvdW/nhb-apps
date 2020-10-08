# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# converteer de gedownloade .html files en maak er 1 .json file van

from django.core.management.base import BaseCommand
import json
import os


class Command(BaseCommand):
    help = "Data van download oude site converteren naar een JSON file"

    JSON_FNAME = 'oude_site.json'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._klasse_data = None
        self._dryrun = False
        self._verbose = True
        self._count_errors = 0
        self._count_warnings = 0
        self._warnings = list()            # al geroepen warnings

    def _roep_warning(self, msg):
        # print en tel waarschuwingen
        # en onderdruk dubbele berichten
        if msg not in self._warnings:
            self._warnings.append(msg)
            self._count_warnings += 1
            self.stdout.write(msg)

    @staticmethod
    def _parse_tabel_cells(data, cells):
        # cellen: rank, schutter, vereniging, AG, scores 1..7, VSG, totaal

        # schutter: [123456] Volledige Naam
        nhb_nr = cells[1][1:1+6]       # afkappen voor veiligheid
        naam = cells[1][9:]

        data[nhb_nr] = schutter_data = dict()
        schutter_data['n'] = naam
        schutter_data['a'] = cells[3]
        schutter_data['s'] = [int(score) for score in cells[4:4 + 7] if score and int(score) > 0]

    def _parse_tabel_regel(self, data, html, pos2, pos_end):
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
                klasse = html[:pos]
                try:
                    self._klasse_data = data[klasse]
                except KeyError:
                    data[klasse] = self._klasse_data = dict()
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

        self._parse_tabel_cells(self._klasse_data, cells)

    def _parse_html_table(self, data, html, pos2, pos_end):
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
                    self._parse_tabel_regel(data, html, pos1, pos2)
                    pos2 += 5
        # while

    def _parse_html(self, data, html):
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
                    if self._verbose:
                        self.stderr.write('[ERROR] Kan einde tabel onverwacht niet vinden')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_html_table(data, html, pos1, pos2)
        # while

    def _read_html(self, fpath, data):
        try:
            html = open(fpath, "r").read()
        except FileNotFoundError:
            self.stderr.write('[ERROR] Failed to open %s' % fpath)
            self._count_errors += 1
        else:
            if self._verbose:
                self.stdout.write("[INFO] Verwerk " + repr(fpath))
            self._parse_html(data, html)

    def _lees_html_in_pad(self, pad, data):
        # filename: YYYYMMDD_HHMMSS_uitslagen
        for afstand in (18, 25):
            data[afstand] = afstand_data = dict()
            fname1 = str(afstand)

            # doe R als laatste ivm verwijderen dubbelen door administratie teamcompetitie
            # (BB/IB/LB wordt met zelfde score onder Recurve gezet)
            for afkorting in ('C', 'BB', 'IB', 'LB', 'R'):
                afstand_data[afkorting] = boog_data = dict()
                fname2 = fname1 + '_' + afkorting + '_rayon'

                for rayon in ('1', '2', '3', '4'):
                    fname3 = fname2 + rayon + ".html"
                    self._read_html(os.path.join(pad, fname3), boog_data)
            # for
        # for

    def _schrijf_json(self, fpath, data):
        fout = os.path.join(fpath, self.JSON_FNAME)
        with open(fout, 'w') as f:
            json.dump(data, f, sort_keys=True)

    def _verwerk_pad(self, fpath):
        data = dict()
        self._lees_html_in_pad(fpath, data)
        self._schrijf_json(fpath, data)

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs=1, help="Pad naar directory met opgehaalde rayonuitslagen")
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        pad = os.path.normpath(options['dir'][0])

        if options['all']:
            # pad wijst naar een top-dir
            # doorloop alle sub-directories
            self._verbose = False
            subdirs = os.listdir(pad)       # geen volgorde garantie
            subdirs.sort()                  # wij willen oudste eerst
            for nr, subdir in enumerate(subdirs):
                self.stdout.write("Voortgang: %s van de %s" % (nr + 1, len(subdirs)))
                fpath = os.path.join(pad, subdir)
                if os.path.isdir(fpath):
                    self._verwerk_pad(fpath)
            # for
        else:
            self._verwerk_pad(pad)

# end of file
