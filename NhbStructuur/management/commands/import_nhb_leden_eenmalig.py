# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer leden gebaseerd op eenmalige dataset uit 2019 """

import argparse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.management.base import BaseCommand
from NhbStructuur.models import NhbLid, NhbVereniging
from .import_utils import check_unexpected_utf8


class Command(BaseCommand):
    help = "Importeer NHB leden uit eenmalige csv"

    def _vind_vereniging(self, vereniging_nr, lid):
        objs = NhbVereniging.objects.filter(nhb_nr=vereniging_nr)
        if len(objs) == 0:
            self.stderr.write("[ERROR] Geen verening met nummer %s voor lid %s" % (repr(vereniging_nr), lid.nhb_nr))
            return None
        if len(objs) != 1:
            self.stderr.write("vind_vereniging: overwacht %s objects" % len(objs))
        return objs[0]

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=argparse.FileType("r"),
                            help="in te lezen bestand")

    def handle(self, *args, **options):
        try:
            lines = options['filename'][0].readlines()
        except UnicodeDecodeError as exc:
            self.stderr.write("Bestand heeft unicode problemen (%s)" % str(exc))
            return

        bulk = list()
        line_nr = 0
        dupe_count = 0
        added_count = 0
        error_count = 0
        for line in lines:
            line_nr += 1
            spl = line.strip().split(";")
            # self.stdout.write(repr(spl))

            # spl = ('165872', 'Winkel',  'van der',    'L.F.',     'Laura', 'vrouw', '2001-11-15', 'demo@gmail.com', '1098')
            #        0         1          2             3           4        5        6             7                 8
            #        nhb_nr    achternaam tussenvoegsel voorletters voornaam geslacht geboren       email             vereniging

            # check for UTF-8 encoding issues
            for part in (spl[1], spl[2], spl[3], spl[4]):
                msg = check_unexpected_utf8(part)
                if msg:
                    self.stderr.write("[WARNING] Line %s: %s" % (line_nr, msg))

            lid = NhbLid()
            try:
                # nhb nr
                lid.nhb_nr = spl[0]

                # naam
                lid.achternaam = spl[1]
                if len(spl[2]):
                    # tussenvoegsel
                    lid.achternaam = spl[2] + " " + lid.achternaam
                if len(spl[4]):
                    lid.voornaam = spl[4]   # voornaam
                else:
                    lid.voornaam = spl[3]   # voorletters

                # geslacht
                if spl[5] == "man":
                    lid.geslacht = NhbLid.GESLACHT[0][0]    # M
                elif spl[5] == "vrouw":
                    lid.geslacht = NhbLid.GESLACHT[1][0]    # V
                else:
                    self.stderr.write("Onbekend geslacht: %s in regel %s" % (repr(spl[5]), line_nr))

                # geboortedatum
                lid.geboorte_datum = parse_date(spl[6]) # Y-M-D

                # email
                lid.email = spl[7]

                # vereniging
                # special: 1368 = bondsburo
                # special: 1377 = persoonlijk lid, geen deelname aan wedstrijden
                if spl[8] not in ('1368', '1377'):
                    lid.bij_vereniging = self._vind_vereniging(spl[8], lid)

                # work-around voor nog niet beschikbare velden
                lid.sinds_datum = parse_date("2000-01-01")
            except ValueError as exc:
                self.stderr.write("Skipping line %s : %s  with unexpected error %s" % (line_nr, repr(line), str(exc)))
                continue    # with the for

            # check if the record already exists
            # note: kijkt niet in bulk
            dupe = NhbLid.objects.filter(
                        nhb_nr=lid.nhb_nr)
            if len(dupe) > 0:
                dupe_count += 1
            else:
                bulk.append(lid)
                added_count += 1
                if len(bulk) >= 100:
                    NhbLid.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk):
            NhbLid.objects.bulk_create(bulk)

        self.stdout.write("Read %s lines; skipped %s dupes; skipped %s errors; added %s records" % (line_nr, dupe_count, error_count, added_count))

# end of file
