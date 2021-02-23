# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# converteer de gedownloade .html files en maak er 1 .json file van

from django.core.management.base import BaseCommand
import hashlib
import json
import os


class Command(BaseCommand):
    help = "Data van download oude site converteren naar een JSON file"

    JSON_FNAME = 'oude_site.json'
    JSON_FNAME_ZELFDE = 'zelfde_site.json'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._klasse_data = None
        self._dryrun = False
        self._verbose = True
        self._count_errors = 0
        self._count_warnings = 0
        self._warnings = list()            # al geroepen warnings

        self._prev_hash = None

    @staticmethod
    def _calc_hash(msg):
        return hashlib.md5(msg.encode('UTF-8')).hexdigest()

    @staticmethod
    def _parse_tabel_regel_vereniging(team_nhb_nrs, html, pos2, pos_end):
        pos = html.find('<td>[', pos2, pos_end)
        if pos < 0:
            # ignore want niet een regel met een bondsnummer / schutter naam
            return

        nhb_nr = html[pos+5:pos+5+6]
        if nhb_nr not in team_nhb_nrs:      # schutters kunnen voor meerdere teams uitkomen
            team_nhb_nrs.append(nhb_nr)

    def _parse_html_table_vereniging(self, team_nhb_nrs, html, pos2, pos_end):
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
                    self.stdout.write('[ERROR] Kan einde regel onverwacht niet vinden (vereniging)')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_tabel_regel_vereniging(team_nhb_nrs, html, pos1, pos2)
                    pos2 += 5
        # while

    def _parse_html_vereniging(self, team_nhb_nrs, html):
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
                        self.stdout.write('[ERROR] Kan einde tabel onverwacht niet vinden (vereniging)')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_html_table_vereniging(team_nhb_nrs, html, pos1, pos2)
        # while

    def _read_html_vereniging(self, fpath, team_nhb_nrs):
        try:
            html = open(fpath, "r", encoding='utf-8').read()
        except FileNotFoundError:               # pragma: no cover
            self.stdout.write('[ERROR] Failed to open %s' % repr(fpath))
            self._count_errors += 1
        except UnicodeDecodeError as exc:       # pragma: no cover
            self.stdout.write('[ERROR] Leesfout %s: %s' % (repr(fpath), str(exc)))
            self._count_errors += 1
        else:
            if self._verbose:
                self.stdout.write("[INFO] Verwerk " + repr(fpath))
            self._parse_html_vereniging(team_nhb_nrs, html)

    @staticmethod
    def _parse_tabel_cells_rayon(data, cells):
        # cellen: rank, schutter, vereniging, AG, scores 1..7, VSG, totaal

        # schutter: [123456] Volledige Naam
        nhb_nr = cells[1][1:1+6]                # nhb nummer

        data[nhb_nr] = schutter_data = dict()
        schutter_data['n'] = cells[1][9:]       # naam (achter nhb_nr)
        schutter_data['a'] = cells[3]           # aanvangsgemiddelde
        schutter_data['v'] = cells[2][1:1+4]    # vereniging nummer
        scores = [int("0"+score_str) for score_str in cells[4:4+7]]
        schutter_data['s'] = scores

    def _parse_tabel_regel_rayon(self, data, html, pos2, pos_end):
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
                self.stdout.write('[ERROR] Kan einde wedstrijdklasse niet vinden: %s' % repr(html))
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
                pos2 = len(html)   # exit while
        # while

        self._parse_tabel_cells_rayon(self._klasse_data, cells)

    def _parse_html_table_rayon(self, data, html, pos2, pos_end):
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
                    self.stdout.write('[ERROR] Kan einde regel onverwacht niet vinden')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_tabel_regel_rayon(data, html, pos1, pos2)
                    pos2 += 5
        # while

    def _parse_html_rayon(self, data, html):
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
                        self.stdout.write('[ERROR] Kan einde tabel onverwacht niet vinden')
                    self._count_errors += 1
                    html = ''
                else:
                    self._parse_html_table_rayon(data, html, pos1, pos2)
        # while

    def _read_html_rayon(self, fpath, data):
        try:
            html = open(fpath, "r", encoding='utf-8').read()
        except FileNotFoundError:               # pragma: no cover
            self.stdout.write('[ERROR] Failed to open %s' % repr(fpath))
            self._count_errors += 1
        except UnicodeDecodeError as exc:       # pragma: no cover
            self.stdout.write('[ERROR] Leesfout %s: %s' % (repr(fpath), str(exc)))
            self._count_errors += 1
        else:
            if self._verbose:
                self.stdout.write("[INFO] Verwerk " + repr(fpath))
            self._parse_html_rayon(data, html)

    @staticmethod
    def _markeer_team_schutters(boog_data, team_nhb_nrs):
        # de schutters staan in hun klasse onder boog_data
        for klasse_data in boog_data.values():
            nhb_nrs = klasse_data.keys()
            for nhb_nr in nhb_nrs:
                if nhb_nr in team_nhb_nrs:
                    # markeer deze schutter als teamschutter
                    schutter_data = klasse_data[nhb_nr]
                    schutter_data['t'] = 1
            # for
        # for

    def _lees_html_in_pad(self, pad, data):
        # filename: YYYYMMDD_HHMMSS_uitslagen
        for afstand in (18, 25):
            data[afstand] = afstand_data = dict()
            fname1 = str(afstand) + '_'

            # doe R als laatste ivm verwijderen dubbelen door administratie teamcompetitie
            # (BB/IB/LB wordt met zelfde score onder Recurve gezet)
            for afkorting in ('C', 'BB', 'IB', 'LB', 'R'):
                afstand_data[afkorting] = boog_data = dict()
                fname2 = fname1 + afkorting

                for rayon in ('1', '2', '3', '4'):
                    fname3 = fname2 + '_rayon' + rayon + ".html"
                    self._read_html_rayon(os.path.join(pad, fname3), boog_data)
                # for

                # zoek alle _vereniging_<ver_nr>.txt
                team_nhb_nrs = list()
                for _, _, fnames in os.walk(pad):
                    for fname in fnames:
                        if '_vereniging_' in fname and fname[:len(fname2)] == fname2:
                            self._read_html_vereniging(os.path.join(pad, fname), team_nhb_nrs)
                    # for
                # for

                self._markeer_team_schutters(boog_data, team_nhb_nrs)
            # for
        # for

    def _schrijf_json(self, fpath, data):
        # verwijder oude json files
        try:
            os.remove(os.path.join(fpath, self.JSON_FNAME))
        except OSError:
            pass

        try:
            os.remove(os.path.join(fpath, self.JSON_FNAME_ZELFDE))
        except OSError:
            pass

        msg = json.dumps(data, sort_keys=True)
        new_hash = self._calc_hash(msg)

        if new_hash == self._prev_hash:
            fout = os.path.join(fpath, self.JSON_FNAME_ZELFDE)
        else:
            fout = os.path.join(fpath, self.JSON_FNAME)
            self._prev_hash = new_hash

        self.stdout.write('[INFO] Schrijf %s' % repr(fout))
        open(fout, 'w').write(msg)

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
            paden = list()
            for subdir in subdirs:
                fpath = os.path.join(pad, subdir)
                if os.path.isdir(fpath):
                    paden.append(fpath)
            # for
            del subdirs
            for nr, pad in enumerate(paden):
                self.stdout.write("Voortgang: %s van de %s" % (nr + 1, len(paden)))
                self._verwerk_pad(pad)
            # for
        else:
            self._verwerk_pad(pad)

# end of file
