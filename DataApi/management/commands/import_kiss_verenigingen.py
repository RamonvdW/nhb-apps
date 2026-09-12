# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer de KISS-bestand met data voor DDI. """

from django.conf import settings
from django.core.management.base import BaseCommand
from DataApi.models import DataApiVereniging
import datetime
import csv
import sys
import os


class Command(BaseCommand):

    help = "Importeer de KISS verenigingen voor DDI"

    def __init__(self):
        super().__init__()
        self.dry_run = True
        self.pad = ''

        self.count_gevonden = 0
        self.count_aangemaakt = 0
        self.count_afgemeld = 0
        self.count_wijzigingen = 0

        self._ver_nr2ver = dict()

        self._gevonden_lid_nrs = list()

    def add_arguments(self, parser):
        parser.add_argument('pad', nargs=1, help="folder waar de KISS .csv bestanden staan")
        parser.add_argument('--dryrun', action='store_true')

    @staticmethod
    def _dmy2ymd(dmy: str) -> str:
        if dmy == '':
            return ''
        # dd-mm-yyyy
        # 01 34 6789
        d = dmy[0:0+2]
        m = dmy[3:3+2]
        y = dmy[6:6+4]
        return y + '-' + m + '-' + d

    @staticmethod
    def _bereken_dagen_tussen_datums(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    def _laad_alle_verenigingen(self):
        self._ver_nr2ver = dict()
        for ver in DataApiVereniging.objects.all():
            self._ver_nr2ver[ver.ver_nr] = ver
        # for

        self.stdout.write('[INFO] %s verenigingen ingeladen' % len(self._ver_nr2ver.keys()))

    def _store_vereniging(self, ver_nr: int, naam: str, status: str, aanmeld_datum: str, kvk_nr: str, straatnaam: str, huis_nr: int, postcode: str, plaats: str):
        ver = self._ver_nr2ver.get(ver_nr, None)
        if ver:
            self.count_gevonden += 1
            assert isinstance(ver, DataApiVereniging)
            if status != 'Actief' and ver.afmeld_datum == '':
                self.stdout.write('[WARNING] Afmelddatum van vereniging %s ontbreekt' % ver_nr)
        else:
            self.count_aangemaakt += 1
            if not self.dry_run:
                ver = DataApiVereniging.objects.create(
                            ver_nr=ver_nr,
                            naam=naam,
                            aanmeld_datum=aanmeld_datum,
                            kvk_nummer=kvk_nr,
                            straatnaam=straatnaam,
                            huisnummer=huis_nr,
                            postcode=postcode,
                            plaats=plaats)
                self._ver_nr2ver[ver_nr] = ver

    def _verwerk_verenigingen(self, data_verenigingen: list):
        # verwijder en check de headers
        regel = data_verenigingen.pop(0)
        # print(repr(regel))
        assert regel == ['Relatienummer', 'Naam', 'Status', 'Oprichtingsdatum', 'KvK Nummer', 'Adres - Straatnaam', 'Adres - Huisnummer', 'Adres - Postcode', 'Adres - Plaatsnaam']

        # voeg de twee datasets samen
        for regel in data_verenigingen:
            ver_nr, naam, status, aanmeld_datum, kvk_nr, straatnaam, huis_nr, postcode, plaats = regel

            # converteer en corrigeer het formaat van de data
            ver_nr = int(ver_nr)
            postcode = postcode.upper().replace(' ', '')        # verwijder de spatie
            aanmeld_datum = self._dmy2ymd(aanmeld_datum)
            if huis_nr:
                huis_nr = int(huis_nr)
            else:
                huis_nr = 0

            self._store_vereniging(ver_nr, naam, status, aanmeld_datum, kvk_nr, straatnaam, huis_nr, postcode, plaats)
        # for

    def _laad_csv_bestand(self, fname) -> list | None:
        fpath = os.path.join(self.pad, fname)
        self.stdout.write('[INFO] Lees %s' % repr(fname))
        data = list()
        try:
            with open(fpath, encoding='raw_unicode_escape') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=';')
                for row in csv_reader:
                    data.append(row)
                # for
            # with
        except IOError as exc:
            self.stdout.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            data = None
        except UnicodeDecodeError as exc:
            self.stdout.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            data = None
        return data

    def _lees_csv_bestanden(self):
        data_verenigingen = self._laad_csv_bestand('all-verenigingen.csv')

        if not data_verenigingen:
            self.stdout.write('Aborting')
            sys.exit(1)

        self._verwerk_verenigingen(data_verenigingen)

        self.stdout.write('[INFO] Samenvatting: %s gevonden, %s aangemaakt, %s afgemeld, %s wijzigingen' %
                          (self.count_gevonden, self.count_aangemaakt, self.count_afgemeld, self.count_wijzigingen))

        count = DataApiVereniging.objects.filter(afmeld_datum='').count()
        self.stdout.write('[INFO] %s actieve verenigingen' % count)

    def handle(self, *args, **options):
        self.pad = options['pad'][0]
        self.dry_run = options['dryrun']

        # Don't turn these signal into exceptions, just die.
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        self._laad_alle_verenigingen()
        self._lees_csv_bestanden()

        self.stdout.write('Done')

# end of file
