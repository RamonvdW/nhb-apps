# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

import argparse
import datetime
from django.core.management.base import BaseCommand
from Records.models import IndivRecord
from NhbStructuur.models import NhbLid
from NhbStructuur.management.commands.import_utils import check_unexpected_utf8


class Command(BaseCommand):
    help = "Importeer individuele records"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=argparse.FileType("r"),
                            help="in te lezen file")
        parser.add_argument('--verbose', action='store_true')

    @staticmethod
    def find_lid(nummer):
        try:
            lid = NhbLid.objects.get(nhb_nr=nummer)
        except NhbLid.DoesNotExist:
            lid = None
        return lid

    def handle(self, *args, **options):
        # self.stderr.write("import individuele competitie historie. args=%s, options=%s" % (repr(args), repr(options)))
        self.verbose = options['verbose']

        try:
            lines = options['filename'][0].readlines()
        except UnicodeDecodeError as exc:
            self.stderr.write("File has format issues (%s)" % str(exc))
            return

        morgen = datetime.datetime.now() + datetime.timedelta(days=1)
        datum_morgen = datetime.date(year=morgen.year, month=morgen.month, day=morgen.day)
        del morgen
        # self.stdout.write("datum_morgen=%s" % repr(datum_morgen))

        bulk = list()
        line_nr = 0
        in_tbody = False
        section = list()
        dupe_count = 0
        added_count = 0
        error_count = 0
        for line in lines:
            line_nr += 1
            line = line.strip()
            if line == '</tbody>':
                in_tbody = False

            if in_tbody:
                # self.stdout.write(repr(line))
                if line[0:0+4] == '<tr ':
                    section = list()
                elif line[0:0+4] == '<td ':
                    line = line.split('>')[1].split('<')[0]
                    section.append(line)
                if line == '</tr>':
                    # self.stdout.write(repr(section))
                    section = [part.strip() for part in section]

                    # section:
                    # ['H', 'S', 'R', 'Outdoor', '70m', '144.192', 'Naam', '03/06/2017', 'Plaats (Land)', '344', 'NL', '954', '']
                    #   0    1    2    3          4      5          6       7             8                9      10    11    12
                    # 9=score
                    # 10=notitie (NL, WR, ER)
                    # 11=uniek volgnummer (binnen dicipline)
                    # 12=tekstversie datum (niet gebruikt)

                    errors = list()
                    record = IndivRecord()

                    # 0: geslacht
                    if section[0] in ('H', 'M', 'h'):
                        record.geslacht = 'M'
                    elif section[0] == 'D':
                        record.geslacht = 'V'
                    else:
                        errors.append("Bad 'geslacht'")

                    # 1: leeftijdscategorie
                    if section[1] in ('M', 'S', 'J', 'C'):
                        record.leeftijdscategorie = section[1]
                    elif section[1] == 'c':
                        record.leeftijdscategorie = 'C'
                    elif section[1] == 'geen bij para':
                        record.leeftijdscategorie = 'U'
                    else:
                        errors.append("Bad 'leeftijdscategorie'")

                    # 2: materiaalklasse
                    if section[2] in ('R', 'C', 'BB', 'IB', 'LB'):
                        record.materiaalklasse = section[2]
                    else:
                        record.materiaalklasse = 'O'
                        record.materiaalklasse_overig = section[2]

                    # 3: dicipline
                    if section[3] == 'Outdoor':
                        record.discipline = 'OD'
                    elif section[3] == 'Indoor':
                        record.discipline = '18'
                    elif section[3] == '25m1p':
                        record.discipline = '25'
                    else:
                        self.stderr.write("Bad 'discipline' in %s" % repr(section))
                        errors.append("Bad 'discipline'")

                    # 4: soort record
                    if len(section[4]) <= 40:
                        record.soort_record = section[4]
                    else:
                        errors.append("Too long 'soort_record'")

                    # 5: nhb nummer
                    nhb_nr = section[5]
                    if len(nhb_nr) == 7:
                        # 123.456
                        nummer = nhb_nr[0:0+3] + nhb_nr[4:4+3]   # 123456
                        record.nhb_lid = self.find_lid(nummer)

                    # 6: schutter naam
                    if len(section[6]) <= 50:
                        record.naam = section[6]
                    else:
                        errors.append("Too long 'name'")

                    # 7: datum
                    try:
                        # 30/06/2017
                        datum = datetime.datetime.strptime(section[7], "%d/%m/%Y")
                    except ValueError:
                        errors.append("Bad 'date' %s" % repr(section[7]))
                    else:
                        record.datum = datetime.date(year=datum.year, month=datum.month, day=datum.day)
                        if record.datum.year < 1950 or record.datum >= datum_morgen:
                            self.stderr.write("[DATA QUALITY] Suspicious year in 'date': %s" % repr(section))

                    # 8: plaats + land
                    plaats = section[8]
                    if ' (' in plaats:
                        spl = plaats.split(' (')
                        record.plaats = spl[0]
                        record.land = spl[1].split(')')[0]
                    else:
                        record.plaats = section[8]
                        record.land = ""

                    # 9: score + notitie
                    spl = section[9].split(" ")
                    try:
                        record.score = int(spl[0])
                    except ValueError:
                        errors.append("Bad 'score'")

                    notitie = section[9][len(spl[0]):].strip()
                    record.score_notitie = notitie

                    # 10: nationaal / europees / wereld record
                    rectype = section[10]
                    if "cancelled" not in rectype:
                        if 'NL' in rectype:
                            record.is_national_record = True
                            rectype = rectype.replace('NL', '')
                        if 'ER' in rectype:
                            record.is_european_record = True
                            rectype = rectype.replace('ER', '')
                        if 'WR' in rectype:
                            record.is_world_record = True
                            rectype = rectype.replace('WR', '')
                        rectype = rectype.replace('en', '')
                        for char in '.,+':
                            rectype = rectype.replace(char, '')
                        rectype = rectype.strip()
                        if rectype:
                            self.stderr.write('[DATA QUALITY] Ignoring suspicious: leftover in record type: %s in section %s' %
                                              (repr(rectype), repr(section)))

                    # 11: volg nummer (uniek binnen dicipline0
                    try:
                        record.volg_nr = int(section[11])
                    except ValueError:
                        errors.append("Bad 'index'")

                    check_unexpected_utf8(record.plaats)
                    check_unexpected_utf8(record.land)
                    check_unexpected_utf8(record.naam)
                    check_unexpected_utf8(record.score_notitie)

                    if len(errors):
                        self.stderr.write("%s in %s" % (" + ".join(errors), repr(section)))
                        error_count += len(errors)
                    else:
                        # check if the record already exists
                        dupe = IndivRecord.objects.filter(
                                    score=record.score,
                                    discipline=record.discipline,
                                    geslacht=record.geslacht,
                                    leeftijdscategorie=record.leeftijdscategorie,
                                    datum=record.datum,
                                    materiaalklasse=record.materiaalklasse)
                        if len(dupe) > 0:
                            dupe_count += 1
                        else:
                            # zorg ervoor dat 'volg_nr' uniek is binnen de dicipline
                            dupe = IndivRecord.objects.filter(volg_nr=record.volg_nr, discipline=record.discipline)
                            if len(dupe) > 0:
                                self.stderr.write("[DATA QUALITY] Ignoring record with reused 'index': %s (in dicipline %s)" %
                                                  (repr(section), repr(record.dicipline)))
                                dupe_count += 1
                            else:
                                bulk.append(record)
                                added_count += 1
                                if len(bulk) >= 100:
                                    IndivRecord.objects.bulk_create(bulk)
                                    bulk = list()
            elif line == '<tbody>':
                in_tbody = True
        # for

        if len(bulk):
            IndivRecord.objects.bulk_create(bulk)

        self.stdout.write("Read %s lines; skipped %s dupes; skipped %s errors; added %s records" %
                          (line_nr, dupe_count, error_count, added_count))

# end of file
