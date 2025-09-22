# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Vergelijk de Nederlandse Records met de administratie van World Archery """

from django.core.management.base import BaseCommand
from django.conf import settings
from Records.models import IndivRecord
import csv


class Command(BaseCommand):         # pragma: no cover      # FUTURE: commando in gebruik nemen en test suite maken
    help = "Check alle NL records tegen de WA administratie (csv)"

    def __init__(self):
        super().__init__()
        self._indiv_indoor = None
        self._indiv_outdoor = None

        self._error_count = 0
        self._warning_count = 0

    def _cache_records(self):
        self._indiv_indoor = (IndivRecord
                              .objects
                              .select_related('sporter')
                              .exclude(discipline='OD'))

        self._indiv_outdoor = (IndivRecord
                               .objects
                               .select_related('sporter')
                               .filter(discipline='OD'))

        self._cache_indiv = dict()        # [indiv.pk] = IndivRecord

        for obj in self._indiv_indoor:
            obj.wa_match = None
            self._cache_indiv[obj.pk] = obj
        # for

        for obj in self._indiv_outdoor:
            obj.wa_match = None
            self._cache_indiv[obj.pk] = obj
        # for

    def _zoek_passend_indiv_record(self, wa_rec):
        # zoek een indiv record dat past bij het WA record

        soort = wa_rec['RecordName']
        soort = soort.replace(' Round', '')
        soort = soort.replace(' metres', 'm')

        sub = wa_rec['RecordSubName']

        if wa_rec['Disc'] == 'Outdoor':
            indiv = self._indiv_outdoor
            if soort == '1440':
                soort = 'WA1440'
            elif soort == '12 arrow Match':
                soort += '50m (12p)'
            elif soort == '15 arrow Match':
                soort = '50m (15p)'

            if sub == '72 arrows':
                soort += ' (72p)'
        else:
            indiv = self._indiv_indoor      # 18m + 25m
            if soort == '12 arrow Match':
                soort = '18m (12p)'
            elif soort == '15 arrow Match':
                soort = '18m (15p)'
            elif sub == '60 arrows':
                soort += ' (60p)'

        if soort not in settings.RECORDS_TOEGESTANE_SOORTEN:
            self.stderr.write(
                '[ERROR] Kan RecordName %s niet vertalen naar een toegestane record_soort (gemaakt: %s)' % (
                    wa_rec['RecordName'], soort))
            self._error_count += 1
            return None

        cat = wa_rec['Cat']
        if cat[0] == 'R':
            mat = 'R'
        elif cat[0] == 'C':
            mat = 'C'
        elif cat[0] == 'B':
            mat = 'BB'
        elif cat[0] == 'I':
            mat = 'IB'
        elif cat[0] == 'L':
            mat = 'LB'
        else:
            self.stderr.write('[ERROR] Kan categorie %s niet vertalen naar materiaalklasse' % cat)
            self._error_count += 1
            return None

        recs = indiv.filter(soort_record=soort,
                            materiaalklasse=mat,
                            score=wa_rec['Points'],
                            x_count=wa_rec['Xs'],
                            max_score=wa_rec['MaxPoints'])

        naam = wa_rec['Naam'].lower()
        for rec in recs:
            if rec.naam.lower() == naam:
                return self._cache_indiv[rec.pk]
        # for

        self.stdout.write('[WARNING] Geen passend KHSN record gevonden: soort=%s' % soort)
        self.stdout.write('          voor %s' % wa_rec)
        for rec in recs:
            self.stdout.write('          Kandidaat: %s' % rec)
        # for
        self._warning_count += 1

        return None

    def _vergelijk_records(self, wa_rec, indiv_rec):
        # para_klasse = models.CharField(max_length=20, blank=True)
        cat = wa_rec['Cat']       # [0]=R/C/etc, [1]=C/J/S, [2]=M/W/O
        if wa_rec['ParaAr'] == 'True':
            # is een para record
            if indiv_rec.para_klasse == '':
                self.stdout.write('[WARNING] Record %s-%s zou een para klasse moeten hebben (WA: cat=%s)' % (
                    indiv_rec.discipline, indiv_rec.volg_nr, cat))
                self._warning_count += 1
        else:
            # is geen para record
            if indiv_rec.para_klasse != '':
                self.stdout.write('[WARNING] Record %s-%s is onverwacht een para klasse (WA: cat=%s)' % (
                    indiv_rec.discipline, indiv_rec.volg_nr, cat))
                self._warning_count += 1

        # geslacht
        if indiv_rec.geslacht == 'M' and 'M' not in cat:
            self.stdout.write('[WARNING] Record %s-%s is onverwacht geslacht=M (WA: cat=%s)' % (
                indiv_rec.discipline, indiv_rec.volg_nr, cat))
            self._warning_count += 1
        elif indiv_rec.geslacht == 'V' and 'W' not in cat:
            self.stdout.write('[WARNING] Record %s-%s is onverwacht geslacht=V (WA: cat=%s)' % (
                indiv_rec.discipline, indiv_rec.volg_nr, cat))
            self._warning_count += 1

        # leeftijdscategorie = models.CharField(max_length=1, choices=LEEFTIJDSCATEGORIE)

        # verbeterbaar = models.BooleanField(default=True)

        # datum = models.DateField()               # dates before 1950 mean "no date known"
        if str(indiv_rec.datum) != wa_rec['Date']:
            self.stdout.write('[WARNING] Record %s-%s heeft andere datum (%s, WA: %s)' % (
                indiv_rec.discipline, indiv_rec.volg_nr, indiv_rec.datum, wa_rec['Date']))
            self._warning_count += 1

        # plaats = models.CharField(max_length=50)
        if wa_rec['Plaats'] != indiv_rec.plaats:
            self.stdout.write('[WARNING] Record %s-%s heeft andere plaats (%s, WA: %s)' % (
                indiv_rec.discipline, indiv_rec.volg_nr, indiv_rec.plaats, wa_rec['Plaats']))
            self._warning_count += 1

        # land = models.CharField(max_length=50)
        # wa_rec['Land'] = 3-letter afkorting!

        # is_european_record = models.BooleanField(default=False)
        if indiv_rec.is_european_record and wa_rec['Type'] not in ('WR', 'ER'):
            # onderdruk bij ER indien ook al WR gematcht
            if not indiv_rec.wa_match:
                self.stdout.write('[WARNING] Record %s-%s heeft ER vlag maar WA type is %s' % (
                    indiv_rec.discipline, indiv_rec.volg_nr, wa_rec['Type']))
                self._warning_count += 1

        # is_world_record = models.BooleanField(default=False)
        if indiv_rec.is_world_record and wa_rec['Type'] != 'WR':
            self.stdout.write('[WARNING] Record %s-%s heeft WR vlag maar WA type is %s' % (
                indiv_rec.discipline, indiv_rec.volg_nr, wa_rec['Type']))
            self._warning_count += 1

    def _read_ned_wa(self, csv_reader):
        eerste = list()
        daarna = list()

        for wa_rec in csv_reader:
            rectype = wa_rec['Type']
            if rectype == 'WR':
                eerste.append(wa_rec)
            else:
                daarna.append(wa_rec)
        # for

        for wa_rec in eerste + daarna:
            indiv_rec = self._zoek_passend_indiv_record(wa_rec)
            if indiv_rec:
                prev_count = self._warning_count

                self._vergelijk_records(wa_rec, indiv_rec)

                if prev_count != self._warning_count:
                    self.stdout.write('          wa_rec=%s' % wa_rec)
                    self.stdout.write('          indiv_rec=%s' % indiv_rec)

                if not indiv_rec.wa_match:
                    indiv_rec.wa_match = wa_rec
        # for

    def _check_onbekende_os_wr_er(self):
        for indiv_rec in self._cache_indiv.values():
            if indiv_rec.is_european_record or indiv_rec.is_world_record:
                if not indiv_rec.wa_match:
                    self.stdout.write('[WARNING] Record %s-%s heeft ER/WR vlag maar geen WA match' % (
                                        indiv_rec.discipline, indiv_rec.volg_nr))
                    self.stdout.write('          indiv_rec=%s' % indiv_rec)
                    self._warning_count += 1
        # for

    def add_arguments(self, parser):
        parser.add_argument('csvfile', nargs=1,
                            help="pad naar de ned_wa.csv file")

    def handle(self, *args, **options):

        # lees all records in zodat we niet steeds naar de database hoeven
        self._cache_records()

        # lees de file in
        fname = options['csvfile'][0]
        try:
            with open(fname, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self._read_ned_wa(csv_reader)
        except IOError as exc:
            self.stderr.write("[ERROR] Kan csv file %s niet lezen (%s)" % (fname, str(exc)))
            return

        self._check_onbekende_os_wr_er()

        self.stdout.write('Vergelijking met WA: %s fouten, %s waarschuwingen' % (self._error_count,
                                                                                 self._warning_count))

        self.stdout.write('Done')

# end of file
