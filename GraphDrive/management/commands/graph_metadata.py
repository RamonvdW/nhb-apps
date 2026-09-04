# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, get_file_metadata
import pprint


class Command(BaseCommand):
    help = "Toon de meta-data van een gedeeld bestand vanuit Sharepoint/Teams"

    def add_arguments(self, parser):
        parser.add_argument('site_index', nargs=1, type=int, help="Welke id's gebruiken? (index in settings.GRAPH_IDS)")
        parser.add_argument('fpath', nargs=1, help="pad naar het bestand")

    def handle(self, *args, **options):
        fpath = options['fpath'][0]

        site = GraphSite(self.stdout)
        if not site.setup(options['site_index'][0]):
            return

        data = get_file_metadata(self.stdout, site, fpath)

        if data:
            out = pprint.pformat(data, indent=4)
            self.stdout.write(out)
        else:
            self.stdout.write('[ERROR] No data')

# end of file
