# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een JSON-file met data uit het CRM-systeem van de bond """

from django.conf import settings
from django.core.management.base import BaseCommand
from Account.models import Account
from ImportCRM.operations import (ImportCrmGeo, ImportCrmFuncties, ImportCrmSporters, ImportCrmSpelden,
                                  ImportCrmLocaties, ImportCrmOpleidingen, ImportCrmVerenigingen)
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_notify_internal_error
from Opleiding.operations import opleiding_post_import_crm
import traceback
import datetime
import logging
import json
import sys

my_logger = logging.getLogger('MH.ImportCRM.import_crm_json')



# expected keys at each level
EXPECTED_DATA_KEYS = ('rayons', 'regions', 'clubs', 'members')
SKIP_VER_NR = (settings.EXTERN_VER_NR,)



class Command(BaseCommand):

    help = "Importeer een JSON file met data uit het CRM systeem van de bond"

    def __init__(self):
        super().__init__()

        self._import_geo = None     # wordt aangemaakt in handle(), nadat dryrun optie bekend is
        self._import_spelden = None
        self._import_functies = None
        self._import_sporters = None
        self._import_locaties = None
        self._import_opleidingen = None
        self._import_verenigingen = None

        self._exit_code = 0

        self._count_errors = 0
        self._count_warnings = 0
        self._count_wijzigingen = 0
        self._count_verwijderingen = 0
        self._count_toevoegingen = 0

        self._count_lid_no_email = 0

        self.dryrun = False

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--sim_now', nargs=1, metavar='YYYY-MM-DD', help="gesimuleerde datum: YYYY-MM-DD")

    def _init_modules(self):
        self._import_geo = ImportCrmGeo(self.stdout, self.dryrun)
        self._import_spelden = ImportCrmSpelden(self.stdout, self.dryrun)
        self._import_functies = ImportCrmFuncties(self.stdout, self.dryrun)
        self._import_sporters = ImportCrmSporters(self.stdout, self.dryrun)
        self._import_locaties = ImportCrmLocaties(self.stdout, self.dryrun)
        self._import_opleidingen = ImportCrmOpleidingen(self.stdout, self.dryrun)
        self._import_verenigingen = ImportCrmVerenigingen(self.stdout, self.dryrun)

        self._import_verenigingen.zet_refs(self._import_geo, self._import_functies, self._import_sporters)
        self._import_opleidingen.zet_refs(self._import_sporters)
        self._import_sporters.zet_refs(self._import_verenigingen)
        self._import_functies.zet_refs(self._import_verenigingen, self._import_sporters)
        self._import_locaties.zet_refs(self._import_verenigingen)
        self._import_spelden.zet_refs(self._import_sporters)

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
        # volgorde is belangrijk!

        self._import_geo.importeer_rayons(data['rayons'])
        self._import_geo.importeer_regios(data['regions'])

        # verenigingen zijn afhankelijk van geo
        self._import_verenigingen.importeer(data['clubs'])

        # locaties zijn afhankelijk van vereniging
        self._import_locaties.importeer(data['clubs'])

        # leden zijn afhankelijk van verenigingen
        self._import_sporters.importeer(data['members'])

        # beheerders zijn afhankelijk van leden en verenigingen
        # secretaris moet voor leden admins
        self._import_verenigingen.importeer_secretaris(data['clubs'])
        self._import_functies.importeer_leden_admins(data['clubs'])

        # genoten opleidingen zijn afhankelijk van sporters
        self._import_opleidingen.importeer(data['members'])

        self._import_spelden.importeer(data['members'])

        self.stdout.write('Import van CRM data is klaar')

    def _report_stats(self):
        # alle tellers optellen
        total_errors = self._count_errors
        total_warnings = self._count_warnings
        total_wijzigingen = self._count_wijzigingen
        total_toevoegingen = self._count_toevoegingen
        total_verwijderingen = self._count_verwijderingen

        for imp_class in (self._import_geo,
                          self._import_spelden,
                          self._import_functies,
                          self._import_sporters,
                          self._import_locaties,
                          self._import_verenigingen):

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
            "%s leden" % (self._import_sporters.count_sporters - self._import_sporters.count_blocked - self._import_sporters.count_admin),
            "%s recent ex-lid" % self._import_sporters.count_blocked,
            "%s langer ex-lid" % self._import_sporters.count_lang_ex_lid,
            "%s recordhouders ex-lid" % self._import_sporters.count_recordhouders,
            "%s uitgeschreven" % self._import_sporters.count_uitgeschreven,
            "%s administratief aanwezig" % self._import_sporters.count_admin,
            "%s speelsterktes" % self._import_spelden.count_sterkte,
            "%s opleiding diploma's" % self._import_opleidingen.count_diplomas,
            "%s verenigingen" % self._import_verenigingen.count_clubs,
            "%s secretarissen zonder account" % self._import_verenigingen.count_sec_no_account,
            "%s regios" % self._import_geo.count_regios,
            "%s rayons" % self._import_geo.count_rayons,
            "%s actieve leden zonder e-mail" % self._import_sporters.count_lid_no_email,
        ]

        if self.dryrun:
            self.stdout.write("\nDRY RUN")
        else:
            schrijf_in_logboek(
                        None, 'CRM-import',
                        'Import van CRM data is uitgevoerd\n' +
                        "Samenvatting: %s" % "; ".join(delen))

        self.stdout.write("\n")
        self.stdout.write("Samenvatting:")
        for deel in delen:
            self.stdout.write('   %s' % deel)
        # for

    def _import_bestand(self, fname):
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
        opleiding_post_import_crm(self.stdout)
        self._report_stats()

        self.stdout.write('Done')

    def handle(self, *args, **options):
        self.dryrun = options['dryrun']
        if self.dryrun:
            self.stdout.write("DRY RUN")

        fname = options['filename'][0]

        self._init_modules()

        if options['sim_now']:
            try:
                sim_now = datetime.datetime.strptime(options['sim_now'][0], '%Y-%m-%d')
            except ValueError as exc:
                self.stdout.write('[ERROR] geen valide sim_now (%s)' % str(exc))
                return
            else:
                self._import_sporters.zet_lidmaatschap_jaar(sim_now)

        self.stdout.write('[INFO] lidmaatschap jaar = %s' % self._import_sporters.lidmaatschap_jaar)

        # vang generieke fouten af
        try:
            self._import_bestand(fname)
        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Unexpected error during import_crm_json\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout (%s) tijdens import_crm_json: %s' % (type(exc), str(exc)))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            self.stdout.write('[WARNING] Stuur crash mail naar ontwikkelaar')
            mailer_notify_internal_error(tb_msg)

            self._exit_code = 1

        if self._exit_code > 0:
            sys.exit(self._exit_code)


# end of file
