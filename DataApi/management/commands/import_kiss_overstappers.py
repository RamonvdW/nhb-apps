# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer de KISS-bestand met data voor DDI. """

from django.core.management.base import BaseCommand
from DataApi.models import DataApiLidmaatschap
import datetime
import csv
import sys
import os


class Command(BaseCommand):

    help = "Importeer de KISS bestanden voor DDI"

    def __init__(self):
        super().__init__()
        self.dry_run = True
        self.csv_fpath = ''
        self.cut_off_date = ''

        self.count_gevonden = 0
        self.count_aangemaakt = 0
        self.count_afgemeld = 0
        self.count_wijzigingen = 0

        self._lidnr2lms = dict()            # [lidnr] = [DataApiLidmaatschap(afmeld_datum=''), ..]
        self._updated_lms = list()          # pk nummers
        self._gevonden_lid_nrs = list()

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="Volledige pad naar het overstappers .csv bestand")
        parser.add_argument('cut_off_date', nargs=1, help='Alles tot en met YYYY-MM-DD verwerken')
        parser.add_argument('--dryrun', action='store_true')

    @staticmethod
    def _dmy2ymd(dmy: str) -> str:
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

    def _laad_alle_actieve_lidmaatschappen(self):
        count_lms = count_leden = 0

        self._lidnr2lms = dict()
        for lms in DataApiLidmaatschap.objects.order_by('aanmeld_datum'):       # oudste eerst
            try:
                self._lidnr2lms[lms.lid_nr].append(lms)
            except KeyError:
                self._lidnr2lms[lms.lid_nr] = [lms]
                count_leden += 1
            count_lms += 1
        # for

        self.stdout.write('[INFO] %s leden met %s lidmaatschappen ingeladen' % (count_leden, count_lms))

    def _overstap_weg_bij_ver(self, lid_nr: int, lms_lijst: list, ver_nr_oud: int, afmeld_datum: str):
        # zoek het lidmaatschap van de oude vereniging
        match_count = 0
        lms_gevonden = None
        for lms in lms_lijst:
            if lms.ver_nr == ver_nr_oud and lms.afmeld_datum == afmeld_datum:
                match_count += 1
                lms_gevonden = lms
        # for

        if match_count != 1:
            match_count = 0
            for lms in lms_lijst:
                if lms.ver_nr == ver_nr_oud and lms.afmeld_datum == '':
                    match_count += 1
                    lms_gevonden = lms
            # for

        if match_count == 0:
            # vereniging niet gevonden (gebeurt in het eerste jaar)
            self.stdout.write('[WARNING] Overstap onduidelijk voor lid %s weg van ver %s' % (lid_nr, ver_nr_oud))
            for lms in lms_lijst:
                self.stdout.write('    %s' % lms)
            # for
            return

        if match_count == 1:
            assert isinstance(lms_gevonden, DataApiLidmaatschap)

            if lms_gevonden.afmeld_datum == afmeld_datum:
                # alles klopt al
                return

            if lms_gevonden.afmeld_datum == '':
                # afmelddatum is bekend geworden
                lms_gevonden.afmeld_datum = afmeld_datum
                if not self.dry_run:
                    lms_gevonden.save(update_fields=['afmeld_datum'])
                self.count_afgemeld += 1
                return

            dagen = self._bereken_dagen_tussen_datums(lms_gevonden.afmeld_datum, afmeld_datum)
            if dagen <= 300:
                # klein correct accepteren we
                lms_gevonden.afmeld_datum = afmeld_datum
                if not self.dry_run:
                    lms_gevonden.save(update_fields=['afmeld_datum'])
                self.count_wijzigingen += 1
                return

            self.stdout.write('[WARNING] Grote correctie (%s dagen) afmelddatum nodig: %s --> %s' % (dagen, lms_gevonden.afmeld_datum, afmeld_datum))
            return

        self.stdout.write('[WARNING] Overstap onduidelijk voor lid %s weg van ver %s afmelddatum %s' % (lid_nr, ver_nr_oud, afmeld_datum))
        for lms in lms_lijst:
            self.stdout.write('    %s' % lms)
        # for

    def _overstap_naar_ver(self, lid_nr: int, lms_lijst: list, ver_nr_nieuw: int, aanmeld_datum: str):
        # zoek het lidmaatschap van de nieuwe vereniging
        match_count = 0
        lms_gevonden = None
        for lms in lms_lijst:
            if lms.afmeld_datum == '' and lms.ver_nr == ver_nr_nieuw:
                match_count += 1
                lms_gevonden = lms
        # for

        if match_count == 0:
            # niet gevonden, dus maak een nieuw lidmaatschap aan

            if len(lms_lijst) == 0:
                self.stdout.write('[WARNING] Overstap van lid %s naar ver %s vanaf %s: niet gevonden' % (lid_nr, ver_nr_nieuw, aanmeld_datum))
                return

            # maak een nieuw record aan
            self.count_aangemaakt += 1

            lms = DataApiLidmaatschap.objects.create(
                        lid_nr=lid_nr,
                        ver_nr=ver_nr_nieuw,
                        aanmeld_datum=aanmeld_datum,
                        afmeld_datum='',
                        land_iso='NL',
                        postcode=lms_lijst[0].postcode,
                        geslacht=lms_lijst[0].geslacht,
                        geboorte_datum=lms_lijst[0].geboorte_datum)

            if not self.dry_run:
                lms.save()

            try:
                self._lidnr2lms[lid_nr].append(lms)
            except KeyError:
                self._lidnr2lms[lid_nr] = [lms]
            return

        if match_count == 1:
            # lms was al aangemaakt en is gevonden
            # controleer de datum van overstap
            assert isinstance(lms_gevonden, DataApiLidmaatschap)

            if lms_gevonden.aanmeld_datum == aanmeld_datum:
                # niets te doen
                return

            if lms_gevonden.afmeld_datum != '':
                self.stdout.write('[WARNING] Overstap lid %s naar ver %s: lms is afgemeld! %s' % (lid_nr, ver_nr_nieuw, lms_gevonden))

            # in de snapshot staat de eerste datum van lms
            # in het overstap bestand staat de exacte datum van lms
            # neem deze dus over
            lms_gevonden.aanmeld_datum = aanmeld_datum
            if not self.dry_run:
                lms_gevonden.save(update_fields=['aanmeld_datum'])
            self.count_wijzigingen += 1
            return

        self.stdout.write('[WARNING] Overstap onduidelijk voor lid %s naar ver %s aanmelddatum %s' % (lid_nr, ver_nr_nieuw, aanmeld_datum))
        for lms in lms_lijst:
            self.stdout.write('    %s' % lms)
        # for

    def _verwerk_overstappers(self, data: list):
        # uit de overstappers lijst kunnen we de exacte datums halen

        if data[0][0] != '#':
            # bij 2022 ontbreekt de eerste kolom
            for regel in data:
                regel.insert(0, '#')
            # for

        regel = data.pop(0)
        assert regel == ['#', 'Lid', 'Lid', 'Vereniging', 'Vereniging', 'Overschrijving', 'Overschrijving', 'Vereniging', 'Vereniging']

        for regel in data:
            _, lid_nr, _, ver_nr_oud, _, afmeld_datum, aanmeld_datum, ver_nr_nieuw, _ = regel

            # data en format conversie
            lid_nr = int(lid_nr)
            ver_nr_oud = int(ver_nr_oud)
            ver_nr_nieuw = int(ver_nr_nieuw)
            afmeld_datum = self._dmy2ymd(afmeld_datum)
            aanmeld_datum = self._dmy2ymd(aanmeld_datum)

            if afmeld_datum > self.cut_off_date:
                # self.stdout.write('[INFO] Skipping %s' % repr(regel))
                continue

            lms_lijst = self._lidnr2lms.get(lid_nr, [])
            if not lms_lijst:
                self.stdout.write('[ERROR] Overstapper %s niet bekend' % lid_nr)
                continue

            if ver_nr_oud == ver_nr_nieuw:
                # self.stdout.write('[INFO] Lid %s stapt over naar dezelfde vereniging %s (ignoring)' % (lid_nr, ver_nr_oud))
                continue

            self._overstap_weg_bij_ver(lid_nr, lms_lijst, ver_nr_oud, afmeld_datum)
            self._overstap_naar_ver(lid_nr, lms_lijst, ver_nr_nieuw, aanmeld_datum)
        # for

    def _laad_csv_bestand(self, fpath) -> list | None:
        fpath = os.path.join(fpath)
        self.stdout.write('[INFO] Lees %s' % repr(fpath))
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
        data_overstappers = self._laad_csv_bestand(self.csv_fpath)

        if not data_overstappers:
            self.stdout.write('Aborting')
            sys.exit(1)

        self._verwerk_overstappers(data_overstappers)

        self.stdout.write('[INFO] Samenvatting: %s gevonden, %s aangemaakt, %s afgemeld, %s wijzigingen' %
                          (self.count_gevonden, self.count_aangemaakt, self.count_afgemeld, self.count_wijzigingen))

        count = DataApiLidmaatschap.objects.filter(afmeld_datum='').count()
        self.stdout.write('[INFO] %s actieve lms' % count)

    def handle(self, *args, **options):
        self.csv_fpath = options['filename'][0]
        self.dry_run = options['dryrun']
        self.cut_off_date = options['cut_off_date'][0]

        # Don't turn these signal into exceptions, just die.
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        self._laad_alle_actieve_lidmaatschappen()
        self._lees_csv_bestanden()

        self.stdout.write('Done')

# end of file
