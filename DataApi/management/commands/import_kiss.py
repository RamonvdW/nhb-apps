# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een KISS-bestand met data uit het CRM-systeem van de bond
    en vergelijk tegen de opgeslagen lidmaatschappen.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from DataApi.models import DataApiLidmaatschap, DataApiVereniging
import csv


class Command(BaseCommand):

    help = "Importeer een JSON file met data uit het CRM systeem van de bond"

    def __init__(self):
        super().__init__()
        self.dry_run = True
        self.afmeld_datum = 'YYYY-MM-DD'
        self.kiss_jaar = 'YYYY'

        self.count_matched = 0
        self.count_niet_gevonden = 0
        self.count_niet_gematcht = 0

        self._vga2lms = dict()      # [(ver_nr, geboorte_datum, aanmeld_datum)] = [DataApiLidmaatschap(afmeld_datum=''), ..]
        self._gpa2lms = dict()      # [(geboorte_datum, postcode, aanmeld_datum)] = [DataApiLidmaatschap(afmeld_datum=''), ..]

        # het meest recent afgemelde lidmaatschap
        self._gpa2afgemeld = dict()     # [(geboorte_datum, postcode, aanmeld_datum)] = DataApiLidmaatschap()

        self._gematchte_lid_nrs = list()

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")
        parser.add_argument('afmeld_datum', nargs=1, help='YYYY-MM-DD te gebruiken voor verdwenen leden/verenigingen')
        parser.add_argument('--dryrun', action='store_true')

    @staticmethod
    def _dmy2ymd(dmy: str) -> str:
        # dd-mm-yyyy
        # 01 34 6789
        d = dmy[0:0+2]
        m = dmy[3:3+2]
        y = dmy[6:6+4]
        return y + '-' + m + '-' + d

    def _load_alle_actieve_lidmaatschappen(self):
        self._gestopte_ver_nrs = list(DataApiVereniging.objects.exclude(afmeld_datum='').values_list('ver_nr', flat=True))
        self._vga2lms = dict()

        for lms in DataApiLidmaatschap.objects.all():
            tup = (lms.ver_nr, lms.geboorte_datum, lms.aanmeld_datum)
            try:
                self._vga2lms[tup].append(lms)
            except KeyError:
                self._vga2lms[tup] = [lms]
        # for

        self._gpa2lms = dict()
        count = 0
        for lms in DataApiLidmaatschap.objects.filter(afmeld_datum=''):
            count += 1

            tup = (lms.geboorte_datum, lms.postcode, lms.aanmeld_datum)
            try:
                self._gpa2lms[tup].append(lms)
            except KeyError:
                self._gpa2lms[tup] = [lms]
        # for
        self.stdout.write('[INFO] %s actieve lidmaatschappen' % count)

        self._gpa2afgemeld = dict()
        for lms in DataApiLidmaatschap.objects.exclude(afmeld_datum='').order_by('afmeld_datum'):
            tup = (lms.geboorte_datum, lms.postcode, lms.aanmeld_datum)
            self._gpa2afgemeld[tup] = lms
        # for
        self.stdout.write('[INFO] %s historische lidmaatschappen' % len(self._gpa2afgemeld.keys()))

    def _zoek_lms(self, geboorte_datum: str, postcode: str, aanmeld_datum: str, ver_nr: int):

        tup = (ver_nr, geboorte_datum, aanmeld_datum)
        lms_lijst = self._vga2lms.get(tup, [])

        # kijk of we ook een postcode match kunnen vinden
        for lms in lms_lijst:
            if lms.postcode == postcode:
                lms_lijst.remove(lms)      # nodig voor tweelingen met dezelfde aanmeld_datum
                return lms
        # for
        if len(lms_lijst) == 1:
            lms = lms_lijst[0]
            lms_lijst.pop(0)    # nodig voor tweelingen met dezelfde aanmeld_datum
            return lms

        if len(lms_lijst) > 1:
            self.stdout.write('[DEBUG] {zoek_lms} te veel vga opties: %s' % repr(lms_lijst))

        # misschien weet het KISS bestand iets wat wij niet wisten
        tup = (0, geboorte_datum, aanmeld_datum)
        lms_lijst = self._vga2lms.get(tup, [])
        for lms in lms_lijst:
            if lms.postcode == postcode:
                self.stdout.write('[INFO] Lid %s ontbrekende ver_nr is %s' % (lms.lid_nr, ver_nr))
                if not self.dry_run:
                    lms.ver_nr = ver_nr
                    lms.save(update_fields=['ver_nr'])

                lms_lijst.remove(lms)    # nodig voor tweelingen met dezelfde aanmeld_datum
                return lms
        # for

        # zoek een actief of recent afgemeld lidmaatschap
        tup = (geboorte_datum, postcode, aanmeld_datum)
        lms_lijst = self._gpa2lms.get(tup, [])
        c = len(lms_lijst)
        if c == 1:
            lms = lms_lijst[0]
            if lms.ver_nr == ver_nr:
                # perfect match
                self.count_matched += 1
                lms_lijst.pop(0)
                return lms

        if c > 1:
            self.stdout.write('[DEBUG] {zoek_lms} multi-uh: %s %s %s %s' % (geboorte_datum, postcode, aanmeld_datum, ver_nr))

        # kijk of het lidmaatschap recent afgelopen is
        tup = (geboorte_datum, postcode, aanmeld_datum)
        lms = self._gpa2afgemeld.get(tup, None)
        if lms:
            assert isinstance(lms, DataApiLidmaatschap)
            if lms.ver_nr == ver_nr:
                self.count_matched += 1
                del self._gpa2afgemeld[tup]
                return lms

        if ver_nr not in self._gestopte_ver_nrs:
            self.stdout.write('[DEBUG] {zoek_lms} uh: %s %s %s %s' % (geboorte_datum, postcode, aanmeld_datum, ver_nr))

        return None


    def _check_lidmaatschappen(self, data: list):
        """
            data is een lijst van regels
            elke regel bevat:
                postcode (nnnn aa)
                geboortedatum (dd-mm-yyyy)
                geslacht (M of V)
                datum begin lidmaatschap (dd-mm-yyyy)
                sporttak (altijd: "handboogsport")
                verenigingscode (nnnn)
        """
        for regel in data[1:]:
            postcode, geboorte_datum, geslacht, aanmeld_datum, sporttak, ver_nr = regel
            postcode = postcode.upper().replace(' ', '')        # verwijder de spatie
            geboorte_datum = self._dmy2ymd(geboorte_datum)
            aanmeld_datum = self._dmy2ymd(aanmeld_datum)
            ver_nr = int(ver_nr)

            # zoek het lidmaatschap
            lms = self._zoek_lms(geboorte_datum, postcode, aanmeld_datum, ver_nr)
            if lms:
                self._gematchte_lid_nrs.append(lms.lid_nr)
                self.count_matched += 1
                continue

            self.count_niet_gevonden += 1
            continue

        self._ver_null_afmelden()
        self._rapporteer_niet_gematcht()

    def _ver_null_afmelden(self):
        qset = DataApiLidmaatschap.objects.filter(afmeld_datum='', ver_nr=0)
        c = qset.count()
        self.stdout.write('[WARNING] %s lidmaatschappen met ver_nr=0 worden nu verwijderd' % c)
        if not self.dry_run:
            qset.delete()

    def _rapporteer_niet_gematcht(self):
        qset = DataApiLidmaatschap.objects.filter(afmeld_datum='').exclude(lid_nr__in=self._gematchte_lid_nrs)
        self.count_niet_gematcht = qset.count()

    def _import_csv_bestand(self, fname):
        self.stdout.write('[INFO] Lees %s' % repr(fname))

        data = list()
        try:
            with open(fname, encoding='raw_unicode_escape') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=';')
                for row in csv_reader:
                    data.append(row)
        except IOError as exc:
            self.stdout.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except UnicodeDecodeError as exc:
            self.stdout.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        self.stdout.write('[INFO] %s regels' % len(data))
        if 'kiss-leden' in fname:
            self._check_lidmaatschappen(data)
        else:
            self.stdout.write('[WARNING] Type bestand niet herkend')

        self.stdout.write('[INFO] Samenvatting: %s gevonden, %s niet gevonden, %s over' %
                            (self.count_matched, self.count_niet_gevonden, self.count_niet_gematcht))

        self.stdout.write('Done')

    def _controleer_dubbele_records(self):
        is_bad = False
        lid_nr2lms = dict()
        for lms in DataApiLidmaatschap.objects.filter(afmeld_datum=''):
            if lms.lid_nr in lid_nr2lms:
                self.stdout.write('[ERROR] %s heeft dubbele records' % lms.lid_nr)
                is_bad = True
            lid_nr2lms[lms.lid_nr] = lms
        # for
        if is_bad:
            krak

    def handle(self, *args, **options):
        fname = options['filename'][0]
        self.dry_run = options['dryrun']

        self.afmeld_datum = options['afmeld_datum'][0]
        if len(self.afmeld_datum) != 10 or self.afmeld_datum[4] != '-' or self.afmeld_datum[7] != '-':
            self.stdout.write('[ERROR] Incorrecte afmeld datum')
        self.kiss_jaar = self.afmeld_datum[:4]

        self._controleer_dubbele_records()
        self._load_alle_actieve_lidmaatschappen()

        self._import_csv_bestand(fname)


# end of file
