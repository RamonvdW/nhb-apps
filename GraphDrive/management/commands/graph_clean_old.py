# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.core.management.base import BaseCommand
from GraphDrive.operations import GraphSite, list_folders_and_files, delete_item

class Command(BaseCommand):
    help = "Begrens het aantal bestanden in de backup folder op een Sharepoint/Teams site"

    def add_arguments(self, parser):
        parser.add_argument('remote_folder', nargs=1, help="pad naar de backup folder")
        parser.add_argument('limiet', nargs=1, type=int, help="maximum aantal bestanden in de folder")

    def handle(self, *args, **options):
        remote_folder = options['remote_folder'][0]
        limiet = options['limiet'][0]

        site = GraphSite(settings.GRAPH_TENANT_ID,
                         settings.GRAPH_SITE_ID,
                         settings.GRAPH_CLIENT_ID,
                         settings.GRAPH_CLIENT_SECRET)

        _, file_lijst = list_folders_and_files(self.stdout, site, remote_folder)
        file_lijst.sort()       # oudste eerst
        self.stdout.write('%-21s %10s %s' % ('modified', 'size', 'name'))
        self.stdout.write('%-21s %10s %s' % ('-'*21, '-'*10, '-'*50))
        for last_mod, size, naam, _ in file_lijst:
            self.stdout.write('%-21s %10s %s' % (last_mod, size, naam))

        if len(file_lijst) < limiet:
            self.stdout.write('[INFO] Niets te verwijderen (er zijn %s bestanden)' % len(file_lijst))
            return

        # verwijder altijd maximaal 5 van de bestanden
        remove_count = 0
        while len(file_lijst) > limiet and remove_count < 5:
            # verwijder oudste bestand
            _, _, naam, item_id = file_lijst.pop(0)
            self.stdout.write('[INFO] Verwijder oudste bestand: %s' % naam)
            delete_item(self.stdout, site, item_id)
            remove_count += 1
        # while

# end of file
