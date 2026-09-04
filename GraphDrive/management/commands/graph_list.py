# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, list_folders_and_files, delete_item

class Command(BaseCommand):
    help = "Toon de inhoud van een folder op een Sharepoint/Teams site"

    def add_arguments(self, parser):
        parser.add_argument('site_index', nargs=1, type=int, help="Welke id's gebruiken? (index in settings.GRAPH_IDS)")
        parser.add_argument('remote_folder', nargs=1, help="pad naar de folder")

    def handle(self, *args, **options):
        remote_folder = options['remote_folder'][0]

        site = GraphSite(self.stdout)
        if not site.setup(options['site_index'][0]):
            return

        dir_lijst, file_lijst = list_folders_and_files(self.stdout, site, remote_folder)

        file_lijst.sort()       # oudste eerst
        self.stdout.write('[INFO] Site: %s' % site.description)

        self.stdout.write('%-21s %10s %s' % ('modified', 'size', 'name'))
        self.stdout.write('%-21s %10s %s' % ('-'*21, '-'*10, '-'*50))
        for naam in dir_lijst:
            self.stdout.write('%-21s %10s %s' % ('(folder)', '', naam))
        # for

        for last_mod, size, naam, _ in file_lijst:
            self.stdout.write('%-21s %10s %s' % (last_mod, size, naam))
        # for

# end of file
