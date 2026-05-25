# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Nederlandse Records importeren en aanpassen vanuit de administratie """

from django.conf import settings
from django.core.management.base import BaseCommand
from BasisTypen.definities import GESLACHT_MAN, GESLACHT_VROUW
from Records.definities import MATERIAALKLASSEN
from Records.models import IndivRecord
from Sporter.models import Sporter
from Logboek.models import schrijf_in_logboek
import openpyxl
import datetime


class Command(BaseCommand):
    help = "Importeer alle records"

    def __init__(self):
        super().__init__()
        self.count_read = 0
        self.count_ongewijzigd = 0
        self.count_errors_skipped = 0
        self.count_andere_errors = 0
        self.count_wijzigingen = 0
        self.count_toegevoegd = 0
        self.count_verwijderd = 0
        self.count_waarschuwing = 0
        self.dryrun = False
        self.verbose = False

        self._oude_volg_nrs = list()
        self._nieuwe_volg_nrs = list()    # voor detecteren dubbel gebruik volgnummers
        self._reported_lid_nrs = list()

        # bereken de datum van morgen, om een check te kunnen doen van een datum
        morgen = datetime.datetime.now() + datetime.timedelta(days=1)
        self.datum_morgen = datetime.date(year=morgen.year, month=morgen.month, day=morgen.day)

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1,
                            help="in te lezen file")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--verbose', action='store_true')

    def _import_indiv_regel(self, row, disc):
        wijzigingen = list()
        errors = list()
        record = IndivRecord()

        if self.verbose:
            self.stdout.write('row: %s' % repr(row))

        # 0 = Index == volg_nr
        curr_record = None
        try:
            val = int(row[0])
        except ValueError:
            errors.append("Foute index (geen nummer): %s" % repr(row[0]))
        else:
            if val in self._nieuwe_volg_nrs:
                errors.append('Volgnummer %s komt meerdere keren voor' % val)
            self._nieuwe_volg_nrs.append(val)

            try:
                curr_record = IndivRecord.objects.get(volg_nr=val, discipline=disc)
            except IndivRecord.DoesNotExist:
                # new record
                pass
            except IndivRecord.MultipleObjectsReturned:  # pragma: no cover
                errors.append('Meerdere records voor %s-%s' % (disc, val))
            else:
                # gevonden, dus voorkom verwijderen
                if val in self._oude_volg_nrs:
                    self._oude_volg_nrs.remove(val)

            if curr_record:
                record.volg_nr = curr_record.volg_nr
                record.discipline = curr_record.discipline
            else:
                record.volg_nr = val
                record.discipline = disc

            # 1 = Geslacht
            # H(eer) / D(ame)
            val = row[1]
            if val == 'H':
                record.geslacht = GESLACHT_MAN
            elif val == 'D':
                record.geslacht = GESLACHT_VROUW
            else:
                errors.append("Fout geslacht: %s" % repr(val))
                val = None
            if val and curr_record:
                if record.geslacht != curr_record.geslacht:
                    wijzigingen.append('geslacht: %s --> %s' % (repr(curr_record.geslacht), repr(record.geslacht)))
                    curr_record.geslacht = record.geslacht

            # 2 = Leeftijdscategorie
            # M(naster) / S(senior) / J(junior) / C(cadet) / nvt = U(uniform)
            # 50+ / 21+ / Onder 21 / Onder 18 / nvt
            val = row[2]
            if val == 'nvt':
                val = 'U'
            elif val == '50+':
                val = 'm'
            elif val == '21+':
                val = 's'
            elif val == 'Onder 21':
                val = 'j'
            elif val == 'Onder 18':
                val = 'c'
            if val in ('M', 'S', 'J', 'C', 'U', 'm', 's', 'j', 'c'):
                record.leeftijdscategorie = val
            else:
                errors.append("Foute leeftijdscategorie': %s" % repr(row[2]))
                val = None
            if val and curr_record:
                if record.leeftijdscategorie != curr_record.leeftijdscategorie:
                    wijzigingen.append('leeftijdscategorie: %s --> %s' % (repr(curr_record.leeftijdscategorie),
                                                                          repr(record.leeftijdscategorie)))
                    curr_record.leeftijdscategorie = record.leeftijdscategorie

            # 3 = Materiaalklasse
            val = row[3]
            if val in MATERIAALKLASSEN:
                record.materiaalklasse = val
            else:
                errors.append("Foute materiaalklasse: %s" % repr(val))
                val = None
            if val and curr_record:
                if record.materiaalklasse != curr_record.materiaalklasse:
                    wijzigingen.append('materiaalklasse: %s --> %s' % (repr(curr_record.materiaalklasse),
                                                                       repr(record.materiaalklasse)))
                    curr_record.materiaalklasse = record.materiaalklasse

            # 4 = Discipline
            # onnodig veld, maar we controleren het toch even
            val = row[4]
            if disc == 'OD' and val == 'Outdoor':
                record.discipline = 'OD'
            elif disc == '18' and val == 'Indoor':
                record.discipline = '18'
            elif disc == '25' and val == '25m1p':
                record.discipline = '25'
            else:
                errors.append("Foute discipline: %s op blad %s" % (repr(val), repr(disc)))

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
                    wijzigingen.append('soort_record: %s --> %s' % (repr(curr_record.soort_record),
                                                                    repr(record.soort_record)))
                    curr_record.soort_record = record.soort_record

            # 6 = Para klasse
            val = row[6][:20]
            if val and val not in settings.RECORDS_TOEGESTANE_PARA_KLASSEN:
                errors.append('Fout in para klasse: %s is niet bekend' % repr(val))
            else:
                record.para_klasse = val
            if curr_record:
                if curr_record.para_klasse != record.para_klasse:
                    wijzigingen.append('para_klasse: %s --> %s' % (repr(curr_record.para_klasse),
                                                                   repr(record.para_klasse)))
                    curr_record.para_klasse = record.para_klasse

            # 7 = Verbeterbaar
            # default = True tenzij er "nee" of "Nee" in het veld staat
            val = row[7]
            record.verbeterbaar = not (val.lower() == 'nee')
            if curr_record and curr_record.verbeterbaar != record.verbeterbaar:
                wijzigingen.append('verbeterbaar: %s --> %s' % (curr_record.verbeterbaar, record.verbeterbaar))
                curr_record.verbeterbaar = record.verbeterbaar

            # 8 = Pijlen
            val = row[8]
            if val:
                try:
                    record.max_score = 10 * int(val)
                except ValueError:
                    errors.append("Fout in pijlen: %s is geen nummer" % repr(val))
                    val = None
                if val and curr_record:
                    if record.max_score != curr_record.max_score:
                        wijzigingen.append('max_score: %s --> %s' % (curr_record.max_score, record.max_score))
                        curr_record.max_score = record.max_score

            # 9 = Bondsnummer
            val = row[9]
            if len(val) == 6:
                # 123456
                try:
                    record.sporter = Sporter.objects.get(lid_nr=val)
                except Sporter.DoesNotExist:
                    # toch door, want niet alle oude leden zitten nog in de database
                    naam = row[10]
                    fout = 'Bondsnummer niet bekend: %s (voor sporter %s)' % (repr(val), repr(naam))
                    if fout not in self._reported_lid_nrs:
                        self._reported_lid_nrs.append(fout)
                        self.stdout.write(fout)
            else:
                errors.append('Fout bondsnummer: %s' % repr(val))
                val = None
            if val and curr_record:
                if record.sporter != curr_record.sporter:
                    wijzigingen.append('sporter: %s --> %s' % (curr_record.sporter, record.sporter))
                    curr_record.sporter = record.sporter

            # 10 = Naam
            val = row[10][:50]
            if record.sporter:
                naam = record.sporter.voornaam + " " + record.sporter.achternaam
                match = 0
                mis = 0
                for part in val.replace('.', ' ').replace('/', ' ').replace(' vd ', ' v d ').split(' '):
                    if part in naam:
                        match += len(part)
                    else:
                        mis += len(part)
                # for
                ok = (match >= 4)  # last name can change significantly after marriage
                if ok:
                    # neem de officiële naam over
                    record.naam = naam
                    if curr_record:
                        if curr_record.naam != record.naam:
                            wijzigingen.append('naam: %s --> %s' % (repr(curr_record.naam), repr(record.naam)))
                            curr_record.naam = record.naam
                else:
                    errors.append('Foute naam: %s maar sporter naam is %s' % (repr(val), repr(naam)))
            else:
                record.naam = val

            # 11 = Datum
            val = row[11]
            if val.upper() == "ONBEKEND":
                record.datum = datetime.date(year=1901, month=1, day=1)
            else:
                val += ' '
                val = val[:val.find(' ')]       # afkappen tussen datum en tijd
                try:
                    # 30-6-2017
                    datum = datetime.datetime.strptime(val, "%Y-%m-%d")
                except ValueError as exc:
                    errors.append("Fout in datum: %s" % str(exc))
                    val = None
                else:
                    record.datum = datum.date()
                    if record.datum.year < 1950 or record.datum >= self.datum_morgen:
                        errors.append("Fout in datum: %s" % repr(val))
                        val = None
            if val and curr_record:
                if curr_record.datum != record.datum:
                    wijzigingen.append('datum: %s --> %s' % (str(curr_record.datum), str(record.datum)))
                    curr_record.datum = record.datum

            # 12 = Plaats
            val = row[12][:50]
            record.plaats = val
            if val and curr_record:
                if curr_record.plaats != record.plaats:
                    wijzigingen.append('plaats: %s --> %s' % (repr(curr_record.plaats), repr(record.plaats)))
                    curr_record.plaats = record.plaats

            # 13 = Land
            val = row[13][:50]
            record.land = val
            if curr_record:
                if curr_record.land != record.land:
                    wijzigingen.append('land: %s --> %s' % (repr(curr_record.land), repr(record.land)))
                    curr_record.land = record.land

            # 14 = Score
            val = row[14]
            try:
                record.score = int(val)
            except ValueError:
                errors.append('Fout in score %s' % repr(val))
                val = None
            if val:
                if record.score > record.max_score:
                    errors.append('Te hoge score voor: %s > %s' % (record.score, record.max_score))
                if curr_record and curr_record.score != record.score:
                    wijzigingen.append('score: %s --> %s' % (repr(curr_record.score), repr(record.score)))
                    curr_record.score = record.score

            if disc in ('OD', '18'):
                # 15 = X-count
                val = row[15]
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

                # 16 = Ook ER
                val = row[16]
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
                        wijzigingen.append('is_european_record: %s --> %s' % (repr(curr_record.is_european_record),
                                                                              repr(record.is_european_record)))
                        curr_record.is_european_record = record.is_european_record

                # 17 = Ook WR
                val = row[17]
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
                        wijzigingen.append('is_world_record: %s --> %s' % (repr(curr_record.is_world_record),
                                                                           repr(record.is_world_record)))
                        curr_record.is_world_record = record.is_world_record

                # 18 = Notities
                val = row[18][:30]
                record.score_notitie = val
                if curr_record:
                    if curr_record.score_notitie != record.score_notitie:
                        wijzigingen.append('score_notitie: %s --> %s' % (repr(curr_record.score_notitie),
                                                                         repr(record.score_notitie)))
                        curr_record.score_notitie = record.score_notitie

            else:
                # blad '25'

                # 15 = Notities
                val = row[15][:30]
                record.score_notitie = val
                if curr_record:
                    if curr_record.score_notitie != record.score_notitie:
                        wijzigingen.append('score_notitie: %s --> %s' % (repr(curr_record.score_notitie),
                                                                         repr(record.score_notitie)))
                        curr_record.score_notitie = record.score_notitie
        # if

        if len(errors):
            self.stdout.write("[ERROR] %s in %s" % (" + ".join(errors), repr(row)))
            self.count_errors_skipped += len(errors)
        else:
            if curr_record:
                if len(wijzigingen):
                    # rapporteer de wijzigingen die we door gaan voeren
                    self.stdout.write(
                        '[INFO] Wijzigingen voor record %s-%s: %s' % (
                            disc, record.volg_nr, "\n          " + "\n          ".join(wijzigingen)))
                    self.count_wijzigingen += len(wijzigingen)
                    if not self.dryrun:
                        curr_record.save()
                else:
                    # ongewijzigd
                    self.count_ongewijzigd += 1
            else:
                # nieuw record
                self.stdout.write("[INFO] Record %s-%s toegevoegd" % (disc, record.volg_nr))
                self.count_toegevoegd += 1
                if not self.dryrun:
                    record.save()

    def _import_indiv_sheet(self, ws, disc):

        self._reported_lid_nrs = list()

        # houd bij welke volg_nrs als in de database zitten
        # als deze niet meer voorkomen, dan moeten we ze verwijderen
        self._oude_volg_nrs = [tup[0] for tup in IndivRecord.objects.filter(discipline=disc).values_list('volg_nr')]

        self._nieuwe_volg_nrs = list()    # voor detecteren dubbel gebruik volgnummers

        row_nr = 0
        for row in ws:
            row_nr += 1

            # skip the header
            if row_nr == 1:
                continue

            row = [str(cell.value) if cell.value is not None else ''
                   for cell in row]

            if row[0]:
                self.count_read += 1
                self._import_indiv_regel(row, disc)
        # for

        # alle overgebleven oude_volg_nrs zijn verwijderd
        if len(self._oude_volg_nrs):
            nrs = repr(self._oude_volg_nrs[:5])
            if len(self._oude_volg_nrs) > 5:
                nrs += ', ...'
            self.stdout.write('[WARNING] %s records worden verwijderd (nummers %s)' % (len(self._oude_volg_nrs), nrs))
        if not self.dryrun:
            for volg_nr in self._oude_volg_nrs:
                IndivRecord.objects.get(discipline=disc, volg_nr=volg_nr).delete()
                self.count_verwijderd += 1
                self.stdout.write("[INFO] Record %s-%s verwijderd" % (disc, volg_nr))
            # for

    def check_consistency(self, disc):
        """ Controleer de consistentie van de records door voor elke soort_record
            te controleren dat de score en de datum aflopen.
        """
        soorten = (IndivRecord
                   .objects
                   .filter(discipline=disc)
                   .distinct('soort_record',
                             'geslacht',
                             'leeftijdscategorie',
                             'materiaalklasse')
                   .values_list('geslacht',
                                'leeftijdscategorie',
                                'materiaalklasse',
                                'soort_record',
                                'para_klasse'))
        for tup in soorten:
            gesl, lcat, makl, srec, para = tup

            # maak de gesorteerde lijst van de records
            # net als RecordsIndivSpecifiekView:get_queryset
            objs = (IndivRecord
                    .objects
                    .filter(geslacht=gesl,
                            discipline=disc,
                            para_klasse=para,
                            soort_record=srec,
                            materiaalklasse=makl,
                            leeftijdscategorie=lcat)
                    .order_by('-datum',
                              '-score'))
            prev_obj = objs[0]
            for obj in objs[1:]:
                if obj.datum == prev_obj.datum and obj.score == prev_obj.score and obj.x_count == prev_obj.x_count:
                    if obj.score_notitie != "gedeeld" or prev_obj.score_notitie != "gedeeld":
                        self.stdout.write("[WARNING] Identieke datum en score voor records %s-%s en %s-%s" % (
                            disc, prev_obj.volg_nr, disc, obj.volg_nr))
                        self.count_waarschuwing += 1
                elif obj.score > prev_obj.score or (obj.score == prev_obj.score and obj.x_count >= prev_obj.x_count):
                    if obj.x_count + prev_obj.x_count > 0:
                        self.stdout.write(
                            "[WARNING] Score niet consecutief voor records %s-%s en %s-%s (%s(%sX) >= %s(%sX))" % (
                                disc, prev_obj.volg_nr, disc, obj.volg_nr,
                                obj.score, obj.x_count, prev_obj.score, prev_obj.x_count))
                        self.count_waarschuwing += 1
                    else:
                        self.stdout.write("[WARNING] Score niet consecutief voor records %s-%s en %s-%s (%s >= %s)" % (
                            disc, prev_obj.volg_nr, disc, obj.volg_nr, obj.score, prev_obj.score))
                        self.count_waarschuwing += 1

                if prev_obj.max_score != obj.max_score:
                    self.stdout.write(
                        '[ERROR] Max score (afgeleide van aantal pijlen) is niet consistent '
                        'in soort %s tussen records %s-%s en %s-%s (%s != %s)' % (
                            repr(srec), disc, prev_obj.volg_nr, disc, obj.volg_nr, prev_obj.max_score, obj.max_score))
                    self.count_andere_errors += 1

                prev_obj = obj
            # for
        # for

    def _import_data(self, wb):
        # doorloop de tabbladen
        bladen = [
            {
                'disc': 'OD',
                'sheet': 'Data individueel outdoor',
                'cols': ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record',
                         'Para klasse', 'Verbeterbaar', 'Pijlen', 'Bondsnummer', 'Naam', 'Datum', 'Plaats', 'Land',
                         'Score', 'X-count', 'Ook ER', 'Ook WR', 'Notities'],
            },
            {
                'disc': '18',
                'sheet': 'Data individueel indoor',
                'cols': ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record',
                         'Para klasse', 'Verbeterbaar', 'Pijlen', 'Bondsnummer', 'Naam', 'Datum', 'Plaats', 'Land',
                         'Score', 'X-count', 'Ook ER', 'Ook WR', 'Notities'],
            },
            {
                'disc': '25',
                'sheet': 'Data individueel 25m1pijl',
                'cols': ['Index', 'Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record',
                         'Para klasse', 'Verbeterbaar', 'Pijlen', 'Bondsnummer', 'Naam', 'Datum', 'Plaats', 'Land',
                         'Score', 'Notities'],
            },
            {
                'disc': 'team',
                'sheet': 'Data team',
                'cols': ['Geslacht', 'Leeftijd', 'Materiaalklasse', 'Discipline', 'Soort_record', 'Verbeterbaar',
                         'Pijlen', 'Bondsnummer', 'Naam', 'Datum', 'Plaats', 'Land', 'Score', 'Notities']
            },
        ]

        for d in bladen:
            sheet_name = d['sheet']
            try:
                ws = wb[sheet_name]
            except KeyError:
                self.stdout.write('[ERROR] Kan sheet %s niet vinden' % repr(sheet_name))
            else:
                self.stdout.write('[INFO] Importeer van blad %s' % repr(sheet_name))

                # check the headers
                row = ws[1]
                row = [cell.value
                       for cell in row]

                while row[-1] is None:
                    row = row[:-1]

                if row != d['cols']:
                    self.stdout.write('[ERROR] Kolom headers kloppen niet:')
                    self.stdout.write('        Verwacht: %s' % repr(d['cols']))
                    self.stdout.write('        Aanwezig: %s' % repr(row))
                    # TODO: hier een mail over sturen naar bondsbureau
                    continue        # met de for

                disc = d['disc']
                if disc in ('OD', '18', '25'):
                    self._import_indiv_sheet(ws, disc)
                    self.check_consistency(disc)
                else:
                    # FUTURE: support voor team records toevoegen
                    self.stdout.write("[TODO] Team records worden nog niet ondersteund")
        # for

        # rapporteer de samenvatting en schrijf deze ook in het logboek
        samenvatting = "Samenvatting: %s records; %s ongewijzigd; %s fouten; %s verwijderd; "\
                       "%s wijzigingen; %s toegevoegd; %s waarschuwingen, %s fouten" % (
                           self.count_read,
                           self.count_ongewijzigd,
                           self.count_errors_skipped,
                           self.count_verwijderd,
                           self.count_wijzigingen,
                           self.count_toegevoegd,
                           self.count_waarschuwing,
                           self.count_andere_errors)

        if self.dryrun:
            self.stdout.write("\nDRY RUN")
        else:
            schrijf_in_logboek(None, 'Records', 'Import uitgevoerd\n' + samenvatting)
            self.stdout.write("\n")

        self.stdout.write(samenvatting)

    def handle(self, *args, **options):
        fname = options['filename'][0]
        self.dryrun = options['dryrun']
        if options['verbose']:
            self.verbose = True

        # lees het excel bestand met alle records
        try:
            wb = openpyxl.load_workbook(fname, read_only=True)
        except (IOError, openpyxl.utils.exceptions.InvalidFileException) as exc:
            self.stdout.write("[ERROR] Kan bestand %s niet lezen (%s)" % (fname, str(exc)))
            return
        else:
            self._import_data(wb)

        self.stdout.write('Done')

# end of file
