# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer de KISS-bestand met data voor DDI. """

from django.conf import settings
from django.core.management.base import BaseCommand
from DataApi.models import DataApiLidmaatschap, DataApiVereniging
import datetime
import csv
import sys
import os


class Command(BaseCommand):

    help = "Importeer de KISS bestanden voor DDI"

    def __init__(self):
        super().__init__()
        self.dry_run = True
        self.pad = ''
        self.jaar = 2000

        self.count_gevonden = 0
        self.count_aangemaakt = 0
        self.count_afgemeld = 0
        self.count_wijzigingen = 0

        self._lidnr2lms = dict()      # [lidnr] = [DataApiLidmaatschap(afmeld_datum=''), ..]

        self._gevonden_lid_nrs = list()

    def add_arguments(self, parser):
        parser.add_argument('pad', nargs=1, help="folder waar de KISS .csv bestanden staan")
        parser.add_argument('jaar', nargs=1, type=int, help="voor welk jaartal inlezen")
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

    def _ver_null_afmelden(self):
        qset = DataApiLidmaatschap.objects.filter(afmeld_datum='', ver_nr=0)
        c = qset.count()
        self.stdout.write('[WARNING] %s lidmaatschappen met ver_nr=0 worden nu verwijderd' % c)
        if not self.dry_run:
            qset.delete()

    def _tel_niet_gematcht(self):
        qset = DataApiLidmaatschap.objects.filter(afmeld_datum='').exclude(lid_nr__in=self._gematchte_lid_nrs)
        self.count_niet_gematcht = qset.count()

    def _overstap_weg_bij_ver(self, lid_nr: int, lms_lijst: list, ver_nr_oud: int, afmeld_datum: str):
        # zoek het lidmaatschap van de oude vereniging
        match_count = 0
        lms_gevonden = None
        for lms in lms_lijst:
            if lms.ver_nr == ver_nr_oud:
                match_count += 1
                lms_gevonden = lms
        # for

        if match_count == 0:
            # vereniging niet gevonden (gebeurt in het eerste jaar)
            if self.jaar != 2021:
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
                self.count_wijzigingen += 1
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
            if lms.ver_nr == ver_nr_nieuw:
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

            if not self.dry_run:
                lms = DataApiLidmaatschap.objects.create(
                    lid_nr=lid_nr,
                    ver_nr=ver_nr_nieuw,
                    aanmeld_datum=aanmeld_datum,
                    afmeld_datum='',
                    land_iso='NL',
                    postcode=lms_lijst[0].postcode,
                    geslacht=lms_lijst[0].geslacht,
                    geboorte_datum=lms_lijst[0].geboorte_datum)
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

            lms_lijst = self._lidnr2lms.get(lid_nr, [])
            if not lms_lijst:
                print('Overstapper %s niet bekend' % lid_nr)
                continue

            self._overstap_weg_bij_ver(lid_nr, lms_lijst, ver_nr_oud, afmeld_datum)
            self._overstap_naar_ver(lid_nr, lms_lijst, ver_nr_nieuw, aanmeld_datum)
        # for

    def _check_update_of_maak_lms(self, lid_nr: int, geboortedatum: str, geslacht: str, postcode: str, ver_nr: int, aanvangsdatum: str):
        lms_lijst = self._lidnr2lms.get(lid_nr, [])
        lms = None
        for lms_lp in lms_lijst:
            if lms_lp.ver_nr == ver_nr:
                # lid kan knipperlicht relatie hebben met vereniging
                # we pakken het nieuwste record
                # TODO: zouden we aanvangsdatum moeten controleren?
                lms = lms_lp
        # for

        if lms:
            self.count_gevonden += 1

            assert isinstance(lms, DataApiLidmaatschap)

            if lms.geboorte_datum != geboortedatum:
                # self.stdout.write('[INFO] Lid %s geboortedatum %s -> %s' % (lid_nr, lms.geboorte_datum, geboortedatum))
                lms.geboorte_datum = geboortedatum
                if not self.dry_run:
                    lms.save(update_fields=['geboorte_datum'])
                self.count_wijzigingen += 1

            if lms.postcode != postcode:
                # self.stdout.write('[INFO] Lid %s postcode %s -> %s' % (lid_nr, lms.postcode, postcode))
                lms.postcode = postcode
                if not self.dry_run:
                    lms.save(update_fields=['postcode'])
                self.count_wijzigingen += 1

            if lms.geslacht != geslacht:
                # self.stdout.write('[INFO] Lid %s geslacht %s -> %s' % (lid_nr, lms.geslacht, geslacht))
                lms.geslacht = geslacht
                if not self.dry_run:
                    lms.save(update_fields=['geslacht'])
                self.count_wijzigingen += 1

            return

        # sluit alle voorgaande lidmaatschappen
        vorige_jaar = self.jaar - 1
        for lms in lms_lijst:
            if lms.afmeld_datum == '':
                lms.afmeld_datum = '%s-12-31' % vorige_jaar
                if not self.dry_run:
                   lms.save(update_fields=['afmeld_datum'])
        # for

        # maak een nieuw record aan
        self.count_aangemaakt += 1

        if not self.dry_run:
            lms = DataApiLidmaatschap.objects.create(
                            lid_nr=lid_nr,
                            ver_nr=ver_nr,
                            aanmeld_datum=aanvangsdatum,
                            afmeld_datum='',
                            geboorte_datum=geboortedatum,
                            geslacht=geslacht,
                            land_iso='NL',
                            postcode=postcode)
            try:
                self._lidnr2lms[lid_nr].append(lms)
            except KeyError:
                self._lidnr2lms[lid_nr] = [lms]

    def _verwerk_leden(self, data_met_ver_nr: list, data_met_lid_nr: list):
        # verwijder en check de headers
        regel = data_met_ver_nr.pop(0)
        assert regel == ['Postcode', 'Geboortedatum', 'Geslacht', 'BondIngangsdatum', 'Sporttak', 'Verenigingscode']
        regel = data_met_lid_nr.pop(0)
        assert regel == ['#', 'Relatienummer', 'Relatienummer', '#', 'Postcode', 'Geboortedatum', 'Geslacht', 'Aanvangsdatum', 'Discipline']

        # voeg de twee datasets samen
        for regel1, regel2, in zip(data_met_ver_nr, data_met_lid_nr):
            postcode, geboortedatum, geslacht, bond_ingangsdatum, _, ver_nr = regel1
            _, lid_nr, _, _, _, _, _, aanvangsdatum, _ = regel2
            assert bond_ingangsdatum == aanvangsdatum

            # converteer en corrigeer het formaat van de data
            postcode = postcode.upper().replace(' ', '')        # verwijder de spatie
            aanvangsdatum = self._dmy2ymd(aanvangsdatum)

            lid_nr = int(lid_nr)
            ver_nr = int(ver_nr)

            self._gevonden_lid_nrs.append(lid_nr)
            self._check_update_of_maak_lms(lid_nr, geboortedatum, geslacht, postcode, ver_nr, aanvangsdatum)
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

    def _verdwenen_lid_nrs_afmelden(self):
        # zoek iedereen met een open lidmaatschap die we niet gevonden hebben in het KISS bestand
        qset = DataApiLidmaatschap.objects.filter(afmeld_datum='').exclude(lid_nr__in=self._gevonden_lid_nrs)
        self.count_afgemeld += qset.count()

        # forceer de afmelddatum
        vorig_jaar = self.jaar - 1
        afmeld_datum = '%s-12-31' % vorig_jaar
        qset.update(afmeld_datum=afmeld_datum)

    def _lees_csv_bestanden(self):
        data_leden_met_ver_nr = self._laad_csv_bestand('kiss-leden-%s.csv' % self.jaar)
        data_leden_met_lid_nr = self._laad_csv_bestand('kiss-leden-met-lidnr-%s.csv' % self.jaar)
        data_overstappers = self._laad_csv_bestand('overstappers-%s.csv' % self.jaar)

        if not (data_leden_met_ver_nr and data_leden_met_lid_nr and data_overstappers):
            self.stdout.write('Aborting')
            sys.exit(1)

        if len(data_leden_met_ver_nr) != len(data_leden_met_lid_nr):
            self.stdout.write('[ERROR] Lijsten zijn niet even lang')
            self.stdout.write('Aborting')
            sys.exit(1)

        self._verwerk_leden(data_leden_met_ver_nr, data_leden_met_lid_nr)
        self._verwerk_overstappers(data_overstappers)
        self._verdwenen_lid_nrs_afmelden()

        self.stdout.write('[INFO] Samenvatting jaar %s: %s gevonden, %s aangemaakt, %s afgemeld, %s wijzigingen' %
                          (self.jaar, self.count_gevonden, self.count_aangemaakt, self.count_afgemeld, self.count_wijzigingen))

        count = DataApiLidmaatschap.objects.filter(afmeld_datum='').count()
        self.stdout.write('[INFO] %s actieve lidmaatschappen' % count)

    def _controleer_dubbele_records(self):
        is_bad = False
        lid_nr2lms = dict()
        for lms in DataApiLidmaatschap.objects.filter(afmeld_datum=''):
            if lms.lid_nr in lid_nr2lms:
                self.stdout.write('[ERROR] %s heeft meerdere open lidmaatschappen' % lms.lid_nr)
                if not is_bad:
                    # eerste keer
                    print(lid_nr2lms[lms.lid_nr])
                    print(lms)
                is_bad = True
            lid_nr2lms[lms.lid_nr] = lms
        # for
        if is_bad:
            self.stdout.write('Aborting')
            sys.exit(1)

    def handle(self, *args, **options):
        self.pad = options['pad'][0]
        self.jaar = options['jaar'][0]
        self.dry_run = options['dryrun']

        # Don't turn these signal into exceptions, just die.
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        self._controleer_dubbele_records()
        self._laad_alle_actieve_lidmaatschappen()
        self._lees_csv_bestanden()

        self.stdout.write('Done')

# end of file
