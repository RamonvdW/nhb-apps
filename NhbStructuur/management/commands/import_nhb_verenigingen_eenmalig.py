# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer verenigingen gebaseerd op eenmalige dataset uit 2019 """

import argparse
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from NhbStructuur.models import NhbVereniging, NhbRegio
from .import_utils import check_unexpected_utf8


def find_regio(regio_nr):
    objs = NhbRegio.objects.filter(regio_nr=regio_nr)
    if len(objs) == 1:
        return objs[0]
    print("find_regio: objs=%s" % repr(objs))
    return objs[0]


class Command(BaseCommand):
    help = "Importeer NHB verenigingen uit eenmalige csv"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=argparse.FileType("r"),
                            help="in te lezen bestand")

    def handle(self, *args, **options):
        try:
            lines = options['filename'][0].readlines()
        except UnicodeDecodeError as exc:
            self.stderr.write("Bestand heeft unicode problemen (%s)" % str(exc))
            return

        new_verenigingen = list()
        bulk = list()
        line_nr = 0
        dupe_count = 0
        added_count = 0
        error_count = 0
        for line in lines:
            line_nr += 1
            # line: NHBNr;Regio;Rayon;Voorvoegsel;Naam;Secretaris;Plaats
            spl = line.strip().split(";")

            # spl = ("1093", "111", "H.B.V. de", "Bosjagers", "demo@gmail.com", "Best")
            #        0       1      2            3            4                 5
            #        nhb_nr  regio  voorzetsel   naam         email             plaats
            # voorzetsel is optioneel
            # email is van de secretaris

            vereniging = NhbVereniging()
            vereniging.nhb_nr = spl[0]
            vereniging.naam = spl[3]
            if len(spl[2]):
                vereniging.naam = spl[2] + " " + vereniging.naam
            vereniging.regio = find_regio(spl[1])
            # email not used
            # plaats not used

            msg = check_unexpected_utf8(vereniging.naam)
            if msg:
                self.stderr.write("[WARNING] Line %s: %s" % (line_nr, msg))

            # kijk of de vereniging al bestaat
            # note: kijkt niet in bulk
            dupe = NhbVereniging.objects.filter(nhb_nr=vereniging.nhb_nr)
            if len(dupe) > 0:
                dupe_count += 1
            else:
                bulk.append(vereniging)
                added_count += 1
                new_verenigingen.append(vereniging.nhb_nr)
                if len(bulk) >= 100:
                    NhbVereniging.objects.bulk_create(bulk)
                    bulk = list()
        # for

        if len(bulk):
            NhbVereniging.objects.bulk_create(bulk)

        # maak de Functies aan voor de CWZ rol
        bulk = list()
        for nhb_nr in new_verenigingen:
            grp = Group()
            grp.name = "CWZ - vereniging %s" % nhb_nr
            bulk.append(grp)
        # for
        Group.objects.bulk_create(bulk)

        self.stdout.write("Read %s lines; skipped %s dupes; skipped %s errors; added %s records" % (line_nr, dupe_count, error_count, added_count))

# end of file
