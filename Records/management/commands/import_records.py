# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

from django.conf import settings
from django.core.management.base import BaseCommand
from Records.models import IndivRecord
from NhbStructuur.models import NhbLid
from Logboek.models import schrijf_in_logboek
import datetime
import json


class Command(BaseCommand):
    help = "Importeer alle records"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1,
                            help="in te lezen file")
        parser.add_argument('--dryrun', action='store_true')

    def _import_indiv(self, sheet, blad):

        for row in sheet['values'][1:]:
            self.count_read += 1

            # remove the extra date column (is hidden in the gsheet)
            if blad in ('OD', '18') and len(row) > 18:
                row = row[:-1]
            elif blad == '25' and len(row) > 16:
                row = row[:-1]

            # laatste colommen volgen niet meer als ze leeg zijn
            # vul aan om verwerken eenvoudig te houden
            while len(row) < 18:
                row.append('')

            wijzigingen = list()
            errors = list()
            record = IndivRecord()

            # 0 = Index
            curr_record = None
            try:
                val = int(row[0])
            except ValueError:
                errors.append("Foute index (geen nummer): %s" % repr(row[0]))
            else:
                try:
                    curr_record = IndivRecord.objects.get(volg_nr=val, discipline=blad)
                except IndivRecord.DoesNotExist:
                    # new record
                    pass
                except IndivRecord.MultipleObjectsReturned:
                    self.stderr.write('[ERROR] Meerdere records voor %s-%s' % (blad, val))

            if curr_record:
                record.volg_nr = curr_record.volg_nr
                record.discipline = curr_record.discipline
            else:
                record.volg_nr = val
                record.discipline = blad

            # 1 = Geslacht
            # H(eer) / D(ame)
            val = row[1]
            if val == 'H':
                record.geslacht = 'M'
            elif val == 'D':
                record.geslacht = 'V'
            else:
                errors.append("Fout geslacht: %s" % repr(val))
                val = None
            if val and curr_record:
                if record.geslacht != curr_record.geslacht:
                    wijzigingen.append('geslacht: %s --> %s' % (repr(curr_record.geslacht), repr(record.geslacht)))
                    curr_record.geslacht = record.geslacht

            # 2 = Leeftijdscategorie
            # S(enior) / J(unior) / C(adet)
            val = row[2]
            if val in ('M', 'S', 'J', 'C'):
                record.leeftijdscategorie = val
            elif val == 'geen bij para':
                record.leeftijdscategorie = 'U'
            else:
                errors.append("Foute leeftijdscategorie': %s" % repr(val))
                val = None
            if val and curr_record:
                if record.leeftijdscategorie != curr_record.leeftijdscategorie:
                    wijzigingen.append('leeftijdscategorie: %s --> %s' % (repr(curr_record.leeftijdscategorie), repr(record.leeftijdscategorie)))
                    curr_record.leeftijdscategorie = record.leeftijdscategorie

            # 3 = Materiaalklasse
            val = row[3]
            if val in ('R', 'C', 'BB', 'IB', 'LB'):
                record.materiaalklasse = val
                record.materiaalklasse_overig = ""
            elif val in ('R staand (Para)',
                         'R Open (Para)', 'C Open (Para)',
                         'C W1', 'C W2', 'R W1', 'R W2'):
                record.materiaalklasse = 'O'
                record.materiaalklasse_overig = val
            else:
                errors.append("Foute materiaalklasse: %s" % repr(val))
                val = None
            if val and curr_record:
                if record.materiaalklasse != curr_record.materiaalklasse:
                    wijzigingen.append('materiaalklasse: %s --> %s' % (repr(curr_record.materiaalklasse), repr(record.materiaalklasse)))
                    curr_record.materiaalklasse = record.materiaalklasse
                if record.materiaalklasse_overig != curr_record.materiaalklasse_overig:
                    wijzigingen.append('materiaalklasse_overig: %s --> %s' % (repr(curr_record.materiaalklasse_overig), repr(record.materiaalklasse_overig)))
                    curr_record.materiaalklasse_overig = record.materiaalklasse_overig

            # 4 = Discipline
            # onnodig veld, maar we controleren het toch even
            val = row[4]
            if blad == 'OD' and val == 'Outdoor':
                record.discipline = 'OD'
            elif blad == '18' and val == 'Indoor':
                record.discipline = '18'
            elif blad == '25' and val == '25m1p':
                record.discipline = '25'
            else:
                errors.append("Foute discipline: %s op blad %s" % (repr(val), repr(blad)))

            # 5 = Soort_record
            # wordt gebruikt om records te categoriseren
            val = row[5][:40]
            if val not in settings.RECORDS_TOEGESTANE_SOORTEN:
                errors.append('Fout in soort_record: %s is niet bekend' % repr(val))
                val = None
            else:
                record.soort_record = val
            if val and curr_record:
                if curr_record.soort_record != record.soort_record:
                    wijzigingen.append('soort_record: %s --> %s' % (repr(curr_record.soort_record), repr(record.soort_record)))
                    curr_record.soort_record = record.soort_record

            # 6 = Afstand
            #val = row[6]
            #if blad == '18':
            #    if val not in ('18', '25', '25+18'):
            #        errors.append("Foute afstand: %s is geen indoor afstand" % repr(val))
            #if blad == '25' and val != '25':
            #    errors.append("Foute afstand: %s moet 25 zijn" % repr(val))
            #if blad == 'OD' and val not in ('30', '40', '50', '60', '70', '90'):
            #    errors.append("Foute afstand: %s is geen outdoor afstand" % repr(val))

            # 7 = Pijlen
            val = row[7]
            if val:
                try:
                    record.max_score = 10 * int(val)
                except ValueError:
                    errors.append("Fout in pijlen: %s is geen nummer" % repr(val))
                    val = None
                if val and curr_record:
                    if record.max_score != curr_record.max_score:
                        if curr_record.max_score != 0:
                            wijzigingen.append('max_score: %s --> %s' % (curr_record.max_score, record.max_score))
                        curr_record.max_score = record.max_score

            # 8 = Bondsnummer
            val = row[8]
            if len(val) == 6:
                # 123456
                try:
                    record.nhb_lid = NhbLid.objects.get(nhb_nr=val)
                except NhbLid.DoesNotExist:
                    # toch door, want niet alle oude leden zitten nog in de database
                    self.stderr.write('NHB nummer niet bekend: %s voor record %s' % (repr(val), repr(row)))
            else:
                errors.append('Fout NHB nummer: %s' % repr(val))
                val = None
            if val and curr_record:
                if record.nhb_lid != curr_record.nhb_lid:
                    wijzigingen.append('nhb_lid: %s --> %s' % (repr(curr_record.nhb_lid), record.nhb_lid))
                    curr_record.nhb_lid = record.nhb_lid

            # 9 = Naam
            val = row[9][:50]
            if record.nhb_lid:
                naam = record.nhb_lid.voornaam + " " + record.nhb_lid.achternaam
                ok = True
                for part in val.replace('.', ' ').replace('/', ' ').replace(' vd ', ' v d ').split(' '):
                    if part not in naam:
                        ok = False
                # for
                if ok:
                    # neem de officiele naam over uit het nhb_lid
                    record.naam = naam
                    if curr_record:
                        if curr_record.naam != record.naam:
                            wijzigingen.append('naam: %s --> %s' % (repr(curr_record.naam), repr(record.naam)))
                            curr_record.naam = record.naam
                else:
                    errors.append('Foute naam: %s moet zijn %s' % (repr(val), repr(naam)))
            else:
                record.naam = val

            # 10 = Datum
            val = row[10]
            try:
                # 30/06/2017
                datum = datetime.datetime.strptime(val, "%d-%m-%Y")
            except ValueError:
                errors.append("Fout in datum: %s" % repr(val))
                val = None
            else:
                record.datum = datetime.date(year=datum.year, month=datum.month, day=datum.day)
                if record.datum.year < 1950 or record.datum >= self.datum_morgen:
                    errors.append("Foute in datum: %s" % repr(val))
                    val = None
            if val and curr_record:
                if curr_record.datum != record.datum:
                    wijzigingen.append('datum: %s --> %s' % (str(curr_record.datum), str(record.datum)))
                    curr_record.datum = record.datum

            # 11 = Plaats
            val = row[11][:50]
            record.plaats = val
            if val and curr_record:
                if curr_record.plaats != record.plaats:
                    wijzigingen.append('plaats: %s --> %s' % (repr(curr_record.plaats), repr(record.plaats)))
                    curr_record.plaats = record.plaats

            # 12 = Land
            val = row[12][:50]
            record.land = val
            if val and curr_record:
                if curr_record.land != record.land:
                    wijzigingen.append('land: %s --> %s' % (repr(curr_record.land), repr(record.land)))
                    curr_record.land = record.land

            # 13 = Score
            val = row[13]
            try:
                record.score = int(val)
            except ValueError:
                errors.append('Fout in score %s' % repr(val))
                val = None
            if val and curr_record:
                if curr_record.score != record.score:
                    wijzigingen.append('score: %s --> %s' % (repr(curr_record.score), repr(record.score)))
                    curr_record.score = record.score

            if blad in ('OD', '18'):
                # 14 = X-count
                val = row[14]
                if val:
                    try:
                        cnt = int(val)
                    except ValueError:
                        errors.append('Fout in X-count %s is geen getal' % repr(val))
                        val = None
                    else:
                        record.x_count = cnt
                if val and curr_record:
                    if curr_record.x_count != record.x_count:
                        wijzigingen.append('x_count: %s --> %s' % (repr(curr_record.x_count), repr(record.x_count)))
                        curr_record.x_count = record.x_count

                # 15 = Ook ER
                val = row[15]
                if val:
                    if val != 'ER':
                        errors.append('Foute tekst in Ook ER: %s' % (repr(val)))
                    else:
                        record.is_european_record = True
                else:
                    # no longer ER
                    record.is_european_record = False

                if curr_record:
                    if curr_record.is_european_record != record.is_european_record:
                        wijzigingen.append('is_european_record: %s --> %s' % (repr(curr_record.is_european_record), repr(record.is_european_record)))
                        curr_record.is_european_record = record.is_european_record

                # 16 = Ook WR
                val = row[16]
                if val:
                    if val != 'WR':
                        errors.append('Foute tekst in Ook WR: %s' % (repr(val)))
                    else:
                        record.is_world_record = True
                else:
                    # no longer ER
                    record.is_world_record = False

                if curr_record:
                    if curr_record.is_world_record != record.is_world_record:
                        wijzigingen.append('is_world_record: %s --> %s' % (repr(curr_record.is_world_record), repr(record.is_world_record)))
                        curr_record.is_world_record = record.is_world_record

                # 17 = Notities
                val = row[17][:30]
                record.score_notitie = val
                if curr_record:
                    if curr_record.score_notitie != record.score_notitie:
                        wijzigingen.append('score_notitie: %s --> %s' % (repr(curr_record.score_notitie), repr(record.score_notitie)))
                        curr_record.score_notitie = record.score_notitie

            elif blad == '25':
                # 14 = Notities
                val = row[14][:30]
                record.score_notitie = val
                if curr_record:
                    if curr_record.score_notitie != record.score_notitie:
                        wijzigingen.append('score_notitie: %s --> %s' % (repr(curr_record.score_notitie), repr(record.score_notitie)))
                        curr_record.score_notitie = record.score_notitie


            if len(errors):
                self.stderr.write("%s in %s" % (" + ".join(errors), repr(row)))
                self.count_errors += len(errors)
            else:
                if curr_record:
                    if len(wijzigingen):
                        # rapporteer de wijzigingen die we door gaan voeren
                        self.stdout.write('[INFO] Wijzigingen voor record %s-%s: %s' % (blad, record.volg_nr, "\n          "+"\n          ".join(wijzigingen)))
                        self.count_wijzigingen += len(wijzigingen)
                        if not self.dryrun:
                            curr_record.save()
                    else:
                        # ongewijzigd
                        self.count_ongewijzigd += 1
                else:
                    # nieuw record
                    self.count_toegevoegd += 1
                    if not self.dryrun:
                        record.save()
        # for

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']

        fname = options['filename'][0]
        #print('fname=%s' % repr(fname))
        with open(fname, 'rb') as jsonfile:
            data = json.load(jsonfile)

        # bereken de datum van morgen, om een check te kunnen doen van een datum
        morgen = datetime.datetime.now() + datetime.timedelta(days=1)
        self.datum_morgen = datetime.date(year=morgen.year, month=morgen.month, day=morgen.day)
        del morgen

        self.count_read = 0
        self.count_ongewijzigd = 0
        self.count_errors = 0
        self.count_wijzigingen = 0
        self.count_toegevoegd = 0

        # doorloop de tabbladen
        for sheet in data['valueRanges']:
            naam = sheet['range']       # 'Tabblad naam'!A1:AF1006
            blad = ''
            if 'Data individueel outdoor' in naam:
                blad = 'OD'
                COLS = ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record', 'Afstand (m)', 'Pijlen', 'Bondsnummer',
                        'Naam', 'Datum', 'Plaats', 'Land', 'Score', 'X-count', 'Ook ER', 'Ook WR', 'Notities']
            elif 'Data individueel indoor' in naam:
                blad = '18'
                COLS = ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record', 'Afstand (m)', 'Pijlen', 'Bondsnummer',
                        'Naam', 'Datum', 'Plaats', 'Land', 'Score', 'X-count', 'Ook ER', 'Ook WR', 'Notities']
            elif 'Data individueel 25m1pijl' in naam:
                blad = '25'
                COLS = ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record', 'Afstand (m)', 'Pijlen', 'Bondsnummer',
                        'Naam', 'Datum', 'Plaats', 'Land', 'Score', 'Notities']
            elif 'Data team' in naam:
                blad = 'team'
                COLS = ['Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record', 'Afstand (m)', 'Pijlen', 'Bondsnummer',
                        'Naam', 'Datum', 'Plaats', 'Land', 'Score', 'Notities']
            else:
                self.stderr.write('[ERROR] Niet ondersteunde tabblad naam: %s' % naam)

            # check the headers
            cols = sheet['values'][0]
            drop = 0
            if cols[-1] == 'Tekstversie datum':
                cols = cols[:-1]
            if cols[-1] == '':
                cols = cols[:-1]
            if cols != COLS:
                self.stderr.write('[ERROR] Kolom headers kloppen niet voor range %s' % naam)
                self.stderr.write('        Verwacht: %s' % repr(COLS))
                self.stderr.write('        Aanwezig: %s' % repr(cols))
            else:
                if blad in ('OD', '18', '25'):
                    self._import_indiv(sheet, blad)
                else:
                    # TODO: support voor team records toevoegen
                    pass
        # for

        # rapporteer de samenvatting en schrijf deze ook in het logboek
        samenvatting = "Samenvatting: %s records ingelezen; %s ongewijzigd; %s overgeslagen ivm errors; %s wijzigingen; %s toegevoegd" %\
                          (self.count_read,
                           self.count_ongewijzigd,
                           self.count_errors,
                           self.count_wijzigingen,
                           self.count_toegevoegd)

        if self.dryrun:
            self.stdout.write("\nDRY RUN")
        else:
            schrijf_in_logboek(None, 'Records', 'Import uitgevoerd\n' + samenvatting)
            self.stdout.write("\n")

        self.stdout.write(samenvatting)

        self.stdout.write('Done')
        return

# end of file
