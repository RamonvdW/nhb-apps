# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een JSON-file met data uit het CRM-systeem van de bond """

from django.conf import settings
from django.core.management.base import BaseCommand
from DataApi.operations import ImportCrmVerenigingen, ImportCrmLidmaatschappen
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_notify_internal_error
import traceback
import logging
import json
import sys

my_logger = logging.getLogger('MH.DataApi.import_histcrm_json')

# expected keys at each level
EXPECTED_DATA_KEYS = ('rayons', 'regions', 'clubs', 'members')
SKIP_VER_NR = (settings.EXTERN_VER_NR,)



class Command(BaseCommand):

    help = "Importeer een JSON file met data uit het CRM systeem van de bond"

    def __init__(self):
        super().__init__()

        self._import_lidmaatschappen = None
        self._import_verenigingen = None

        self.dryrun = True
        self._include_ver_null = False
        self._exit_code = 0

        self._count_errors = 0
        self._count_warnings = 0
        self._count_wijzigingen = 0
        self._count_verwijderingen = 0
        self._count_toevoegingen = 0

        self.aanmelddatum = ''
        self.afmelddatum = ''
        self.forceer_mutatie_datum = ''

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")
        parser.add_argument('aanmelddatum', nargs=1, help='YYYY-MM-DD te gebruiken voor nieuwe leden/verenigingen')
        parser.add_argument('afmelddatum', nargs=1, help='YYYY-MM-DD te gebruiken voor verdwenen leden/verenigingen')
        parser.add_argument('mutatie_datum', nargs=1, help='YYYY-MM-DD geforceerde mutatie moment')
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--include_ver_null', action='store_true')

    def _init_modules(self):
        self._import_verenigingen = ImportCrmVerenigingen(self.stdout, self.dryrun, self._include_ver_null,
                                                          self.aanmelddatum, self.afmelddatum,
                                                          self.forceer_mutatie_datum)
        self._import_lidmaatschappen = ImportCrmLidmaatschappen(self.stdout, self.dryrun, self._include_ver_null,
                                                                self.aanmelddatum, self.afmelddatum,
                                                                self.forceer_mutatie_datum)

    def _check_keys(self, keys, expected_keys, level):
        has_error = False
        keys = list(keys)
        for key in expected_keys:
            try:
                keys.remove(key)
            except ValueError:
                self.stdout.write("[ERROR] [FATAL] Verplichte sleutel %s niet aanwezig in de %s data" % (
                                    repr(key), repr(level)))
                self._exit_code = 2
                has_error = True
        # for
        if len(keys):
            self.stdout.write("[WARNING] Extra sleutel aanwezig in de %s data: %s" % (repr(level), repr(keys)))
            self._count_warnings += 1
        return has_error

    def _import_data(self, data: dict):
        # volgorde is belangrijk
        self._import_verenigingen.importeer(data['clubs'])

        self._import_lidmaatschappen.zet_ver_nrs(self._import_verenigingen.get_ver_nrs())
        self._import_lidmaatschappen.importeer(data['members'], self.forceer_mutatie_datum)

        self.stdout.write('Import van historische CRM data is klaar')

    def _report_stats(self):
        # alle tellers optellen
        total_errors = self._count_errors
        total_warnings = self._count_warnings
        total_wijzigingen = self._count_wijzigingen
        total_toevoegingen = self._count_toevoegingen
        total_verwijderingen = self._count_verwijderingen

        for imp_class in (self._import_verenigingen,
                          self._import_lidmaatschappen):

            total_errors += imp_class.count_errors
            total_warnings += imp_class.count_warnings
            total_wijzigingen += imp_class.count_wijzigingen
            total_toevoegingen += imp_class.count_toevoegingen
            total_verwijderingen += imp_class.count_verwijderingen
        # for

        # rapporteer de samenvatting en schrijf deze ook in het logboek
        delen = [
            "%s fouten" % total_errors,
            "%s waarschuwingen" % total_warnings,
            "%s nieuw" % total_toevoegingen,
            "%s wijzigingen" % total_wijzigingen,
            "%s verwijderingen" % total_verwijderingen,
            "%s actieve verenigingen" % self._import_verenigingen.count_actief,
            "%s actieve lidmaatschappen" % self._import_lidmaatschappen.count_actief,
            "%s gestopte verenigingen" % self._import_verenigingen.count_gestopt,
            "%s gestopte lidmaatschappen" % self._import_lidmaatschappen.count_gestopt,
            "%s lidmaatschappen bij onbekende vereniging" % self._import_lidmaatschappen.count_ver_null,
        ]

        if self.dryrun:
            self.stdout.write("\nDRY RUN")
        else:
            schrijf_in_logboek(
                        None, 'CRM-import',
                        'Import van historische CRM data voor DDI is uitgevoerd\n' +
                        "Samenvatting: %s" % "; ".join(delen))

        self.stdout.write("\n")
        self.stdout.write("Samenvatting:")
        for deel in delen:
            self.stdout.write('   %s' % deel)
        # for

    def _import_bestand(self, fname):
        self.stdout.write('[INFO] Lees %s' % repr(fname))

        try:
            with open(fname, encoding='raw_unicode_escape') as f_handle:
                data = json.load(f_handle)
        except IOError as exc:
            self.stdout.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except json.decoder.JSONDecodeError as exc:
            self.stdout.write("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return
        except UnicodeDecodeError as exc:
            self.stdout.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        if self._check_keys(data.keys(), EXPECTED_DATA_KEYS, "top-level"):
            return

        for key in EXPECTED_DATA_KEYS:
            if len(data[key]) < 1:
                self.stdout.write("[ERROR] Geen data voor top-level sleutel %s" % repr(key))
                return

        self._import_data(data)
        self._report_stats()

        self.stdout.write('Done')

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']
        self._include_ver_null = options['include_ver_null']

        fname = options['filename'][0]
        self.aanmelddatum = options['aanmelddatum'][0]
        self.afmelddatum = options['afmelddatum'][0]
        self.forceer_mutatie_datum = options['mutatie_datum'][0]

        self._init_modules()

        # vang generieke fouten af
        try:
            self._import_bestand(fname)
        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Unexpected error during import_histcrm_json\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout (%s) tijdens import_histcrm_json: %s' % (type(exc), str(exc)))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            # TODO: re-enable
            # self.stdout.write('[WARNING] Stuur crash mail naar ontwikkelaar')
            # mailer_notify_internal_error(tb_msg)

            self._exit_code = 1

        if self._exit_code > 0:
            sys.exit(self._exit_code)


# end of file
