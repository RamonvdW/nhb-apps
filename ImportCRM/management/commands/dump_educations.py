# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" importeer een JSON-file met data uit het CRM-systeem van de bond """

from django.core.management.base import BaseCommand
import traceback
import json
import sys


class Command(BaseCommand):

    help = "Dump de opleidingen uit de JSON file met data uit het CRM systeem van de bond"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="pad naar het JSON bestand")

    def _import_members(self, data):
        """ doorloop de data van de leden """
        for member in data:
            lid_nr = member['member_number']

            # "educations": [
            #    {"code": "011", "name": "HANDBOOGTRAINER A", "date_start": "1990-01-01", "date_stop": "1990-01-01"},
            try:
                edus = member['educations']
            except KeyError:
                # geen opleidingen
                pass
            else:
                for edu in edus:
                    code = edu['code']
                    date_start = edu['date_start']
                    date_stop = edu['date_stop']
                    self.stdout.write("%s %s %s %s" % (lid_nr, code, date_start, date_stop))
                # for

        # for member

    def _import_bestand(self, fname):
        try:
            with open(fname, encoding='raw_unicode_escape') as f_handle:
                data = json.load(f_handle)
        except IOError as exc:
            self.stderr.write("[ERROR] Bestand kan niet gelezen worden (%s)" % str(exc))
            return
        except json.decoder.JSONDecodeError as exc:
            self.stderr.write("[ERROR] Probleem met het JSON formaat in bestand %s (%s)" % (repr(fname), str(exc)))
            return
        except UnicodeDecodeError as exc:
            self.stderr.write("[ERROR] Bestand heeft unicode problemen (%s)" % str(exc))
            return

        self._import_members(data['members'])

    def handle(self, *args, **options):

        fname = options['filename'][0]

        # vang generieke fouten af
        try:
            self._import_bestand(fname)
        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])

            self.stderr.write('[ERROR] Onverwachte fout tijdens import_crm_json: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))


# end of file
